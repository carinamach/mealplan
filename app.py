import json
from pathlib import Path

from flask import Flask, render_template


app = Flask(__name__)
RECIPES_FILE = Path(__file__).parent / "seed_data" / "recipes.json"


def load_recipes():
    """Read the predefined recipes from the JSON data file."""
    with RECIPES_FILE.open(encoding="utf-8") as recipe_file:
        return json.load(recipe_file)


@app.route("/")
def home():
    """Display the application's home page."""
    return render_template("index.html")


@app.route("/recipes")
def recipes():
    """Display all predefined recipes."""
    return render_template("recipes.html", recipes=load_recipes())


if __name__ == "__main__":
    app.run(debug=True)
