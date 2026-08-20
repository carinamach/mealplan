import json
import unittest
from pathlib import Path

from recipe_filters import filter_recipes, matches_dietary_preference


RECIPES_FILE = Path(__file__).parent / "seed_data" / "recipes.json"


def load_recipes():
    with RECIPES_FILE.open(encoding="utf-8") as recipe_file:
        return json.load(recipe_file)


class RecipeFilterTests(unittest.TestCase):
    def test_meal_type_filter_returns_only_that_type(self):
        breakfast_recipes = filter_recipes(load_recipes(), meal_type="breakfast")

        self.assertTrue(breakfast_recipes)
        self.assertTrue(all(recipe["meal_type"] == "breakfast" for recipe in breakfast_recipes))

    def test_vegetarian_filter_hides_meat_and_fish(self):
        recipes = load_recipes()
        vegetarian_recipes = filter_recipes(recipes, preferences=["vegetarian"])
        names = {recipe["name"] for recipe in vegetarian_recipes}

        self.assertIn("Apple cinnamon porridge", names)
        self.assertNotIn("Chicken avocado wrap", names)
        self.assertNotIn("Smoked salmon bagel", names)
        self.assertTrue(all(matches_dietary_preference(recipe, "vegetarian") for recipe in vegetarian_recipes))

    def test_vegan_filter_uses_tags_and_ingredients(self):
        vegan_recipes = filter_recipes(load_recipes(), preferences=["vegan"])
        names = {recipe["name"] for recipe in vegan_recipes}

        self.assertIn("Vegetable tofu curry", names)
        self.assertNotIn("Tomato feta omelette", names)
        self.assertNotIn("Apple peanut butter snack", names)


if __name__ == "__main__":
    unittest.main()
