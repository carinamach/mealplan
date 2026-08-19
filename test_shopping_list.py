import unittest

from shopping_list import build_shopping_list, categorize_ingredient


class ShoppingListTests(unittest.TestCase):
    def test_identical_ingredients_are_combined(self):
        meals = {
            "Lunch": {
                "ingredients": [
                    {"name": "chicken breast", "amount": 500, "unit": "g"},
                    {"name": "rice", "amount": 200, "unit": "g"},
                ]
            },
            "Dinner": {
                "ingredients": [
                    {"name": "chicken breast", "amount": 300, "unit": "g"},
                ]
            },
        }

        shopping_list = dict(build_shopping_list(meals))
        chicken = next(item for item in shopping_list["Meat & fish"] if item["name"] == "chicken breast")

        self.assertEqual(chicken["amount"], "800")
        self.assertEqual(chicken["unit"], "g")

    def test_ingredients_are_grouped_into_simple_categories(self):
        meals = {
            "Breakfast": {
                "ingredients": [
                    {"name": "apple", "amount": 1, "unit": ""},
                    {"name": "milk", "amount": 250, "unit": "ml"},
                    {"name": "spinach", "amount": 40, "unit": "g"},
                    {"name": "rolled oats", "amount": 60, "unit": "g"},
                ]
            }
        }

        shopping_list = dict(build_shopping_list(meals))

        self.assertEqual(categorize_ingredient("smoked salmon"), "Meat & fish")
        self.assertEqual([item["name"] for item in shopping_list["Fruit"]], ["apple"])
        self.assertEqual([item["name"] for item in shopping_list["Dairy"]], ["milk"])
        self.assertEqual([item["name"] for item in shopping_list["Vegetables"]], ["spinach"])
        self.assertEqual([item["name"] for item in shopping_list["Pantry"]], ["rolled oats"])

    def test_missing_meals_are_ignored(self):
        meals = {
            "Breakfast": {"ingredients": [{"name": "banana", "amount": 1, "unit": ""}]},
            "Snack": None,
        }

        shopping_list = dict(build_shopping_list(meals))
        self.assertEqual(shopping_list["Fruit"][0]["name"], "banana")


if __name__ == "__main__":
    unittest.main()
