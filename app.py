import json
import os
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, session, url_for

from calculations import calculate_targets
from meal_planner import calculate_plan_totals, find_swap_recipe, generate_daily_plan
from recipe_filters import MEAL_TYPES, filter_recipes
from shopping_list import build_shopping_list


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

    return render_template("meal_plan.html", plan=plan, targets=targets)


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


@app.route("/shopping-list")
def shopping_list():
    """Display a combined shopping list from the saved meal plan."""
    plan = session.get("meal_plan")
    grouped_items = build_shopping_list(plan["meals"]) if plan else []
    return render_template("shopping_list.html", shopping_list=grouped_items)


if __name__ == "__main__":
    app.run(debug=True)
