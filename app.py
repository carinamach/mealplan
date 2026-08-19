import json
import os
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, session, url_for

from calculations import calculate_targets


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
            return redirect(url_for("profile"))
        except (KeyError, ValueError) as exception:
            error = str(exception)

    return render_template(
        "profile.html",
        profile=session.get("profile", {}),
        targets=session.get("targets"),
        error=error,
    )


if __name__ == "__main__":
    app.run(debug=True)
