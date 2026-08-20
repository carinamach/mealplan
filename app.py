import json
import os
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, session, url_for

from calculations import calculate_targets
from meal_planner import WEEKDAYS, calculate_plan_totals, find_swap_recipe, generate_daily_plan, generate_weekly_plan
from recipe_filters import MEAL_TYPES, filter_recipes
from shopping_list import build_shopping_list, build_weekly_shopping_list


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-development-key")
RECIPES_FILE = Path(__file__).parent / "seed_data" / "recipes.json"


def load_recipes():
    """Read the predefined recipes from the JSON data file."""
    with RECIPES_FILE.open(encoding="utf-8") as recipe_file:
        return json.load(recipe_file)


def get_recipe(recipe_id):
    """Return one recipe by its id, or stop with a 404 page if it is missing."""
    recipe = next((recipe for recipe in load_recipes() if recipe["id"] == recipe_id), None)

    if recipe is None:
        abort(404)

    return recipe


def get_favorite_ids():
    """Return favorite recipe ids stored in the session."""
    return [int(recipe_id) for recipe_id in session.get("favorites", [])]


@app.route("/")
def home():
    """Display the application's home page."""
    return render_template("index.html")


@app.route("/recipes")
def recipes():
    """Display recipes, optionally filtered by meal type and dietary preferences."""
    meal_type = request.args.get("meal_type") or None
    search_query = request.args.get("q", "")
    profile_data = session.get("profile") or {}
    dietary_preferences = profile_data.get("dietary_preferences") or []
    apply_diet_filter = request.args.get("match_diet") == "1" and bool(dietary_preferences)
    filtered_recipes = filter_recipes(
        load_recipes(),
        meal_type=meal_type,
        preferences=dietary_preferences if apply_diet_filter else None,
        query=search_query,
    )
    return render_template(
        "recipes.html",
        recipes=filtered_recipes,
        meal_types=MEAL_TYPES,
        selected_meal_type=meal_type if meal_type in MEAL_TYPES else None,
        dietary_preferences=dietary_preferences,
        match_diet=apply_diet_filter,
        search_query=search_query,
        favorite_ids=set(get_favorite_ids()),
    )


@app.route("/recipes/<int:recipe_id>")
def recipe_detail(recipe_id):
    """Display one recipe with its ingredients and instructions."""
    return render_template("recipe_detail.html", recipe=get_recipe(recipe_id))


@app.post("/recipes/<int:recipe_id>/favorite")
def toggle_favorite(recipe_id):
    """Add or remove a recipe id from the session favorites list."""
    get_recipe(recipe_id)
    favorite_ids = get_favorite_ids()

    if recipe_id in favorite_ids:
        favorite_ids.remove(recipe_id)
    else:
        favorite_ids.append(recipe_id)

    session["favorites"] = favorite_ids
    return redirect(request.referrer or url_for("recipes"))


@app.route("/favorites")
def favorites():
    """Display recipes the user has marked as favorites."""
    favorite_ids = get_favorite_ids()
    recipes_by_id = {recipe["id"]: recipe for recipe in load_recipes()}
    favorite_recipes = [recipes_by_id[recipe_id] for recipe_id in favorite_ids if recipe_id in recipes_by_id]
    return render_template("favorites.html", recipes=favorite_recipes, favorite_ids=set(favorite_ids))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    """Save a simple profile in the session and show estimated targets."""
    error = None

    if request.method == "POST":
        try:
            profile_data = {
                "age": int(request.form["age"]),
                "height": float(request.form["height"]),
                "weight": float(request.form["weight"]),
                "target_weight": float(request.form["target_weight"]),
                "biological_sex": request.form["biological_sex"],
                "activity_level": request.form["activity_level"],
                "goal": request.form["goal"],
                "dietary_preferences": request.form.getlist("dietary_preferences"),
            }

            if (
                profile_data["age"] < 13
                or profile_data["height"] <= 0
                or profile_data["weight"] <= 0
                or profile_data["target_weight"] <= 0
            ):
                raise ValueError("Enter a valid age, height, current weight, and target weight.")

            session["profile"] = profile_data
            session["targets"] = calculate_targets(
                age=profile_data["age"],
                height=profile_data["height"],
                weight=profile_data["weight"],
                activity_level=profile_data["activity_level"],
                goal=profile_data["goal"],
                biological_sex=profile_data["biological_sex"],
            )
            session.pop("meal_plan", None)
            session.pop("weekly_plan", None)
            return redirect(url_for("profile"))
        except (KeyError, ValueError) as exception:
            error = str(exception)

    return render_template(
        "profile.html",
        profile=session.get("profile", {}),
        targets=session.get("targets"),
        error=error,
    )


@app.route("/meal-plan")
def meal_plan():
    """Display a simple daily plan based on the saved profile estimates."""
    targets = session.get("targets")
    profile_data = session.get("profile")

    if not targets or not profile_data:
        return render_template("meal_plan.html", plan=None)

    plan = session.get("meal_plan")
    if plan is None:
        plan = generate_daily_plan(
            load_recipes(),
            calorie_target=targets["calories"],
            goal=profile_data["goal"],
        )
        session["meal_plan"] = plan

    # Also ensure a weekly plan exists in session for the combined page.
    weekly = session.get("weekly_plan")
    if weekly is None:
        weekly = generate_weekly_plan(
            load_recipes(),
            calorie_target=targets["calories"],
            goal=profile_data["goal"],
        )
        session["weekly_plan"] = weekly

    # Portions stored per-meal for daily plan
    portions = session.get("meal_plan_portions", {})
    # Portions stored per-day+meal for weekly plan
    weekly_portions = session.get("weekly_plan_portions", {})

    return render_template("meal_plan.html", plan=plan, weekly_plan=weekly, weekdays=WEEKDAYS, targets=targets, portions=portions, weekly_portions=weekly_portions)


@app.post('/meal-plan/portions/<meal_name>')
def set_meal_portions(meal_name):
    """Set how many portions the user plans to cook for one meal (AJAX JSON).

    Returns updated per-portion and total calories/protein for that meal and
    updated daily totals.
    """
    if not request.is_json:
        abort(400)

    data = request.get_json() or {}
    try:
        portions_value = int(data.get('portions', 1))
    except Exception:
        portions_value = 1

    plan = session.get('meal_plan')
    if not plan or meal_name not in plan['meals']:
        abort(404)

    recipe = plan['meals'][meal_name]
    if not recipe:
        abort(404)

    # store portions in session
    portions = session.get('meal_plan_portions', {})
    portions[meal_name] = max(1, portions_value)
    session['meal_plan_portions'] = portions

    # compute per-portion and totals
    servings = recipe.get('servings', 1) or 1
    per_portion_cal = recipe['calories'] / servings
    per_portion_protein = recipe['protein'] / servings
    total_cal = per_portion_cal * portions[meal_name]
    total_protein = per_portion_protein * portions[meal_name]

    # recalc daily totals accounting for portions
    daily_cal = 0
    daily_protein = 0
    for m, r in plan['meals'].items():
        if not r:
            continue
        p = portions.get(m, 1)
        s = r.get('servings', 1) or 1
        cal_per = r['calories'] / s
        prot_per = r['protein'] / s
        daily_cal += cal_per * p
        daily_protein += prot_per * p

    # update session plan totals (keep original plan structure for other uses)
    session['meal_plan_totals'] = {'total_calories': daily_cal, 'total_protein': daily_protein}

    return {
        'meal': {
            'per_portion_calories': round(per_portion_cal, 1),
            'per_portion_protein': round(per_portion_protein, 1),
            'total_calories': round(total_cal, 1),
            'total_protein': round(total_protein, 1),
        },
        'daily_totals': {
            'total_calories': round(daily_cal, 1),
            'total_protein': round(daily_protein, 1),
        }
    }


@app.post("/meal-plan/swap/<meal_name>")
def swap_meal(meal_name):
    """Swap one meal while keeping the rest of the saved plan unchanged."""
    plan = session.get("meal_plan")
    profile_data = session.get("profile")

    if not plan or not profile_data or meal_name not in plan["meals"]:
        abort(404)

    current_recipe = plan["meals"][meal_name]
    if current_recipe is None:
        abort(404)

    alternative = find_swap_recipe(current_recipe, load_recipes(), profile_data["goal"])
    if alternative:
        plan["meals"][meal_name] = alternative
        plan.update(calculate_plan_totals(plan["meals"]))
        session["meal_plan"] = plan

    return redirect(url_for("meal_plan"))


@app.route("/weekly-plan")
def weekly_plan():
    # Weekly plan was merged into the daily meal-plan page; redirect there.
    return redirect(url_for('meal_plan'))


@app.post("/weekly-plan/swap/<day>/<meal_name>")
def swap_weekly_meal(day, meal_name):
    """Swap one meal in the saved weekly plan for the given day and meal."""
    plan = session.get("weekly_plan")
    profile_data = session.get("profile")

    if not plan or not profile_data or day not in plan:
        abort(404)

    day_plan = plan[day]
    if meal_name not in day_plan["meals"]:
        abort(404)

    current_recipe = day_plan["meals"][meal_name]
    if current_recipe is None:
        abort(404)

    # If the client posted a specific recipe id (AJAX), use it.
    if request.is_json:
        data = request.get_json() or {}
        recipe_id = data.get("recipe_id")
        if recipe_id:
            try:
                chosen = get_recipe(int(recipe_id))
            except Exception:
                return ("Not found", 404)
            day_plan["meals"][meal_name] = chosen
            day_plan.update(calculate_plan_totals(day_plan["meals"]))
            session["weekly_plan"] = plan
            return {
                "meal": {
                    "id": chosen["id"],
                    "name": chosen["name"],
                    "calories": chosen["calories"],
                    "protein": chosen["protein"],
                    "url": url_for("recipe_detail", recipe_id=chosen["id"]),
                },
                "totals": {
                    "total_calories": day_plan["total_calories"],
                    "total_protein": day_plan["total_protein"],
                },
            }

    # Fallback for non-AJAX: pick an automatic alternative and redirect.
    alternative = find_swap_recipe(current_recipe, load_recipes(), profile_data["goal"])
    if alternative:
        day_plan["meals"][meal_name] = alternative
        day_plan.update(calculate_plan_totals(day_plan["meals"]))
        session["weekly_plan"] = plan

    return redirect(url_for("weekly_plan"))


@app.post("/weekly-plan/portions/<day>/<meal_name>")
def set_weekly_portions(day, meal_name):
    """Set how many portions the user plans to cook for one weekly meal (AJAX JSON)."""
    if not request.is_json:
        abort(400)

    data = request.get_json() or {}
    try:
        portions_value = int(data.get('portions', 1))
    except Exception:
        portions_value = 1

    weekly = session.get('weekly_plan')
    if not weekly or day not in weekly:
        abort(404)

    day_plan = weekly[day]
    if meal_name not in day_plan.get('meals', {}):
        abort(404)

    # store portions in session
    weekly_portions = session.get('weekly_plan_portions', {})
    weekly_portions.setdefault(day, {})[meal_name] = max(1, portions_value)
    session['weekly_plan_portions'] = weekly_portions

    # recompute day totals accounting for portions
    total_cal = 0
    total_protein = 0
    for m, r in day_plan['meals'].items():
        if not r:
            continue
        p = weekly_portions.get(day, {}).get(m, 1)
        s = r.get('servings', 1) or 1
        cal_per = r['calories'] / s
        prot_per = r['protein'] / s
        total_cal += cal_per * p
        total_protein += prot_per * p

    # save updated totals in session weekly_plan as well
    day_plan['total_calories'] = total_cal
    day_plan['total_protein'] = total_protein
    session['weekly_plan'] = weekly

    return {
        'day_totals': {
            'total_calories': round(total_cal, 1),
            'total_protein': round(total_protein, 1),
        },
        'portions': weekly_portions.get(day, {}).get(meal_name, 1)
    }


@app.route("/weekly-plan/alternatives/<day>/<meal_name>")
def weekly_alternatives(day, meal_name):
    """Return JSON alternatives for a given day and meal to power the swap UI."""
    plan = session.get("weekly_plan")
    profile_data = session.get("profile")

    if not plan or not profile_data or day not in plan:
        abort(404)

    day_plan = plan[day]
    current = day_plan["meals"].get(meal_name)
    if not current:
        return ([], 200)

    # Find same-type alternatives, exclude current id
    candidates = [r for r in load_recipes() if r["meal_type"] == current["meal_type"] and r["id"] != current["id"]]

    # Return up to 5 alternatives sorted by closeness in calories
    candidates.sort(key=lambda r: abs(r["calories"] - current["calories"]))
    results = []
    for r in candidates[:5]:
        results.append({
            "id": r["id"],
            "name": r["name"],
            "calories": r["calories"],
            "protein": r["protein"],
            "url": url_for("recipe_detail", recipe_id=r["id"]),
        })

    return {"alternatives": results}


@app.post("/weekly-plan/reset")
def reset_weekly_plan():
    """Reset the weekly plan and portion selections back to generated defaults."""
    profile_data = session.get("profile")
    targets = session.get("targets")

    if not profile_data or not targets:
        # Nothing to reset if no profile/targets saved
        return ("No profile", 400)

    # Regenerate weekly plan using the same logic as meal_plan view
    weekly = generate_weekly_plan(
        load_recipes(),
        calorie_target=targets["calories"],
        goal=profile_data["goal"],
    )
    session["weekly_plan"] = weekly

    # Clear any saved weekly portions so UI shows default (1)
    session.pop("weekly_plan_portions", None)

    return {"status": "ok"}


@app.post('/weekly-plan/mealprep')
def make_weekmealprep():
    """Copy one day's meals across the whole weekly plan to make meal-prepping easier.

    Expects JSON { source_day: 'Monday' } (case-sensitive names from WEEKDAYS). If missing, uses 'Monday'.
    """
    if not request.is_json:
        return ("Expected JSON", 400)

    data = request.get_json() or {}
    source_day = data.get('source_day', 'Monday')

    weekly = session.get('weekly_plan')
    if not weekly or source_day not in weekly:
        return ("No weekly plan or invalid source day", 400)

    source_plan = weekly[source_day]
    # Copy meals (deep copy minimal fields) to every day
    for day in list(weekly.keys()):
        # shallow copy of dict structure; recipes are dicts already
        weekly[day]['meals'] = {m: source_plan['meals'].get(m) for m in source_plan['meals'].keys()}
        weekly[day].update(calculate_plan_totals(weekly[day]['meals']))

    session['weekly_plan'] = weekly
    # Optionally clear weekly portions to default
    session.pop('weekly_plan_portions', None)

    return { 'status': 'ok' }


@app.route("/shopping-list")
def shopping_list():
    """Display a combined shopping list from the saved meal plan."""
    # Prefer a saved weekly plan if available; otherwise fall back to the daily plan.
    weekly = session.get("weekly_plan")
    if weekly:
        portions_map = session.get('weekly_plan_portions', {})
        grouped_items, portions = build_weekly_shopping_list(weekly, portions_map=portions_map)
        return render_template("shopping_list.html", shopping_list=grouped_items, portions=portions, weekly=True)

    plan = session.get("meal_plan")
    portions_map = session.get('meal_plan_portions', {})
    grouped_items = build_shopping_list(plan["meals"], portions=portions_map) if plan else []
    # compute total planned portions for display
    total_portions = sum(int(v) for v in (portions_map.values() or [1])) if portions_map else (len(plan["meals"]) if plan else 0)
    return render_template("shopping_list.html", shopping_list=grouped_items, portions=total_portions, weekly=False)


if __name__ == "__main__":
    app.run(debug=True)
