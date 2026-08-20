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

    def test_recipe_detail_page_has_meal_prep_controls(self):
        client = app.test_client()
        response = client.get("/recipes/1")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"How many servings do you want to make?", response.data)
        self.assertIn(b"data-original-servings", response.data)


class ProfileTest(unittest.TestCase):
    def test_profile_saves_target_weight_and_preferences(self):
        client = app.test_client()
        response = client.post(
            "/profile",
            data={
                "age": "30",
                "height": "170",
                "weight": "70",
                "target_weight": "65",
                "biological_sex": "female",
                "activity_level": "moderate",
                "goal": "lose_weight",
                "dietary_preferences": ["vegetarian", "gluten-free"],
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Target weight (kg)", response.data)

        with client.session_transaction() as saved_session:
            self.assertEqual(saved_session["profile"]["target_weight"], 65.0)
            self.assertEqual(
                saved_session["profile"]["dietary_preferences"],
                ["vegetarian", "gluten-free"],
            )

    def test_swap_changes_only_the_selected_meal_in_session(self):
        client = app.test_client()
        client.post(
            "/profile",
            data={
                "age": "30",
                "height": "170",
                "weight": "70",
                "target_weight": "65",
                "biological_sex": "female",
                "activity_level": "moderate",
                "goal": "high_protein",
            },
        )
        client.get("/meal-plan")

        with client.session_transaction() as saved_session:
            original_breakfast_id = saved_session["meal_plan"]["meals"]["Breakfast"]["id"]
            original_lunch_id = saved_session["meal_plan"]["meals"]["Lunch"]["id"]

        response = client.post("/meal-plan/swap/Breakfast", follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        with client.session_transaction() as saved_session:
            self.assertNotEqual(saved_session["meal_plan"]["meals"]["Breakfast"]["id"], original_breakfast_id)
            self.assertEqual(saved_session["meal_plan"]["meals"]["Lunch"]["id"], original_lunch_id)


class ShoppingListPageTest(unittest.TestCase):
    def test_shopping_list_page_shows_combined_ingredients(self):
        client = app.test_client()
        client.post(
            "/profile",
            data={
                "age": "30",
                "height": "170",
                "weight": "70",
                "target_weight": "65",
                "biological_sex": "female",
                "activity_level": "moderate",
                "goal": "high_protein",
            },
        )
        client.get("/meal-plan")
        response = client.get("/shopping-list")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Shopping list", response.data)
        self.assertIn(b'type="checkbox"', response.data)
        self.assertTrue(
            any(category in response.data for category in (b"Meat &amp; fish", b"Vegetables", b"Fruit", b"Dairy", b"Pantry"))
        )


class RecipePageFilterTest(unittest.TestCase):
    def test_recipes_page_can_filter_by_meal_type(self):
        client = app.test_client()
        response = client.get("/recipes?meal_type=breakfast")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Apple cinnamon porridge", response.data)
        self.assertNotIn(b"Chicken avocado wrap", response.data)

    def test_recipes_page_can_filter_by_saved_dietary_preferences(self):
        client = app.test_client()
        client.post(
            "/profile",
            data={
                "age": "30",
                "height": "170",
                "weight": "70",
                "target_weight": "65",
                "biological_sex": "female",
                "activity_level": "moderate",
                "goal": "lose_weight",
                "dietary_preferences": ["vegetarian"],
            },
        )
        response = client.get("/recipes?match_diet=1")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Apple cinnamon porridge", response.data)
        self.assertNotIn(b"Chicken avocado wrap", response.data)


if __name__ == "__main__":
    unittest.main()
