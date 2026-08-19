import json
import os
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, session, url_for

from calculations import calculate_targets
from meal_planner import calculate_plan_totals, find_swap_recipe, generate_daily_plan
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


@app.route("/")
def home():
    """Display the application's home page."""
    return render_template("index.html")


@app.route("/recipes")
def recipes():
    """Display all predefined recipes."""
    return render_template("recipes.html", recipes=load_recipes())


@app.route("/recipes/<int:recipe_id>")
def recipe_detail(recipe_id):
    """Display one recipe with its ingredients and instructions."""
    return render_template("recipe_detail.html", recipe=get_recipe(recipe_id))


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
