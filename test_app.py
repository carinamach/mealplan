import unittest

from app import app, load_recipes


class RecipeInstructionsTest(unittest.TestCase):
    def test_recipe_data_contains_instructions(self):
        recipes = load_recipes()

        self.assertTrue(recipes)
        self.assertTrue(
            all("instructions" in recipe and recipe["instructions"] for recipe in recipes),
            "Every recipe should include preparation instructions.",
        )

    def test_recipe_detail_page_displays_instructions(self):
        client = app.test_client()
        response = client.get("/recipes/1")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Instructions", response.data)


if __name__ == "__main__":
    unittest.main()
