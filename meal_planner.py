"""Simple meal-plan selection using the predefined recipe data."""

from copy import deepcopy
from itertools import product


WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def calculate_plan_totals(meals):
    """Calculate totals from the recipes currently selected in a plan."""
    selected_recipes = [recipe for recipe in meals.values() if recipe]
    return {
        "total_calories": sum(recipe["calories"] for recipe in selected_recipes),
        "total_protein": sum(recipe["protein"] for recipe in selected_recipes),
    }


def find_swap_recipe(current_recipe, recipes, goal):
    """Find a same-type alternative that is close in calories and suits the goal."""
    alternatives = [
        recipe
        for recipe in recipes
        if recipe["meal_type"] == current_recipe["meal_type"] and recipe["id"] != current_recipe["id"]
    ]

    if not alternatives:
        return None

    def swap_score(recipe):
        calorie_difference = abs(recipe["calories"] - current_recipe["calories"])

        if goal == "high_protein":
            goal_score = -recipe["protein"]
        elif goal in ("lose_weight", "low_calorie"):
            goal_score = recipe["calories"]
        else:
            goal_score = 0

        return calorie_difference, goal_score

    return min(alternatives, key=swap_score)


def generate_daily_plan(recipes, calorie_target, goal):
    """Choose the recipe combination closest to the daily calorie target.

    The recipe collection is small, so trying every breakfast/lunch/dinner/snack
    combination is easy to understand and fast enough for this project.
    """
    meals_by_type = {
        "breakfast": [recipe for recipe in recipes if recipe["meal_type"] == "breakfast"],
        "lunch": [recipe for recipe in recipes if recipe["meal_type"] == "lunch"],
        "dinner": [recipe for recipe in recipes if recipe["meal_type"] == "dinner"],
        "snack": [recipe for recipe in recipes if recipe["meal_type"] == "snack"],
    }

    if not all(meals_by_type[meal_type] for meal_type in ("breakfast", "lunch", "dinner")):
        raise ValueError("Recipes are needed for breakfast, lunch, and dinner.")

    best_plan = None
    best_score = None

    # None means that a snack is optional, not required.
    for breakfast, lunch, dinner, snack in product(
        meals_by_type["breakfast"],
        meals_by_type["lunch"],
        meals_by_type["dinner"],
        [None, *meals_by_type["snack"]],
    ):
        selected_recipes = [breakfast, lunch, dinner]
        if snack:
            selected_recipes.append(snack)

        totals = calculate_plan_totals(
            {
                "Breakfast": breakfast,
                "Lunch": lunch,
                "Dinner": dinner,
                "Snack": snack,
            }
        )
        total_calories = totals["total_calories"]
        total_protein = totals["total_protein"]

        # High-protein plans prefer more protein only when calorie closeness is equal.
        score = (abs(total_calories - calorie_target), -total_protein if goal == "high_protein" else 0)

        if best_score is None or score < best_score:
            best_score = score
            best_plan = {
                "meals": {
                    "Breakfast": breakfast,
                    "Lunch": lunch,
                    "Dinner": dinner,
                    "Snack": snack,
                },
                **totals,
            }

    return best_plan


def generate_weekly_plan(recipes, calorie_target, goal):
    """Build a Monday–Sunday plan with some variation between days.

    Instead of repeating the same daily plan for every weekday, generate a
    daily plan for each day and remove the chosen recipes from the working
    pool so subsequent days favor different recipes. If the pool becomes
    insufficient for a required meal type, fall back to the full recipe set.
    """
    recipes_pool = list(recipes)
    weekly = {}

    for day in WEEKDAYS:
        try:
            daily = generate_daily_plan(recipes_pool, calorie_target, goal)
        except ValueError:
            # Not enough variety left in the pool; reset and try again.
            recipes_pool = list(recipes)
            daily = generate_daily_plan(recipes_pool, calorie_target, goal)

        weekly[day] = deepcopy(daily)

        # Remove selected recipes from the pool to encourage variety.
        chosen = [r for r in daily["meals"].values() if r]
        for r in chosen:
            recipes_pool = [rec for rec in recipes_pool if rec["id"] != r["id"]]

        # If pool empties, reset so remaining days can still be filled.
        if not recipes_pool:
            recipes_pool = list(recipes)

    return weekly
