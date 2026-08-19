import unittest

from app import load_recipes
from meal_planner import generate_daily_plan


class MealPlannerTests(unittest.TestCase):
    def test_daily_plan_has_required_meals_and_correct_totals(self):
        plan = generate_daily_plan(load_recipes(), 1800, "maintain_weight")

        self.assertIsNotNone(plan["meals"]["Breakfast"])
        self.assertIsNotNone(plan["meals"]["Lunch"])
        self.assertIsNotNone(plan["meals"]["Dinner"])

        selected_recipes = [recipe for recipe in plan["meals"].values() if recipe]
        self.assertEqual(plan["total_calories"], sum(recipe["calories"] for recipe in selected_recipes))
        self.assertEqual(plan["total_protein"], sum(recipe["protein"] for recipe in selected_recipes))

    def test_plan_can_be_compared_with_calorie_target(self):
        plan = generate_daily_plan(load_recipes(), 2200, "maintain_weight")

        remaining_calories = 2200 - plan["total_calories"]
        self.assertGreater(remaining_calories, 0)


if __name__ == "__main__":
    unittest.main()
