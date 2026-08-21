"""Simple meal-plan selection using the predefined recipe data."""

from copy import deepcopy
from itertools import product


def calculate_plan_totals(meals):
    """Calculate daily totals from one portion of each selected meal."""

    total_calories = 0
    total_protein = 0

    for recipe in meals.values():
        if not recipe:
            continue

        total_calories += recipe.get("calories", 0)
        total_protein += recipe.get("protein", 0)

    return {
        "total_calories": round(total_calories),
        "total_protein": round(total_protein, 1),
    }

def find_swap_recipe(current_recipe, recipes, goal):
    """Find a same-type alternative that is close in calories and suits the goal."""

    alternatives = [
        recipe
        for recipe in recipes
        if (
            recipe["meal_type"] == current_recipe["meal_type"]
            and recipe["id"] != current_recipe["id"]
        )
    ]

    if not alternatives:
        return None

    def swap_score(recipe):
        current_servings = current_recipe.get("servings", 1) or 1
        recipe_servings = recipe.get("servings", 1) or 1

        current_calories = current_recipe.get("calories", 0) / current_servings
        recipe_calories = recipe.get("calories", 0) / recipe_servings

        calorie_difference = abs(recipe_calories - current_calories)

        if goal == "high_protein":
            goal_score = -(recipe.get("protein", 0) / recipe_servings)
        elif goal in ("lose_weight", "low_calorie"):
            goal_score = recipe_calories
        else:
            goal_score = 0

        return calorie_difference, goal_score

    return min(alternatives, key=swap_score)


def generate_daily_plan(recipes, calorie_target, goal):
    """
    Choose breakfast, lunch, dinner and optionally a snack.

    The combination is selected based on calories per portion.
    The algorithm first prefers combinations that reach the calorie target.
    Among those, it chooses the combination with the smallest calorie surplus.

    If no combination reaches the target, it chooses the combination
    that gets closest to the target from below.
    """

    meals_by_type = {
        "breakfast": [
            recipe
            for recipe in recipes
            if recipe["meal_type"] == "breakfast"
        ],
        "lunch": [
            recipe
            for recipe in recipes
            if recipe["meal_type"] == "lunch"
        ],
        "dinner": [
            recipe
            for recipe in recipes
            if recipe["meal_type"] == "dinner"
        ],
        "snack": [
            recipe
            for recipe in recipes
            if recipe["meal_type"] == "snack"
        ],
    }

    if not all(
        meals_by_type[meal_type]
        for meal_type in ("breakfast", "lunch", "dinner")
    ):
        raise ValueError(
            "Recipes are needed for breakfast, lunch, and dinner."
        )

    best_plan = None
    best_score = None

    # A snack is optional.
    snack_options = [None] + meals_by_type["snack"]

    for breakfast, lunch, dinner, snack in product(
        meals_by_type["breakfast"],
        meals_by_type["lunch"],
        meals_by_type["dinner"],
        snack_options,
    ):
        meals = {
            "Breakfast": breakfast,
            "Lunch": lunch,
            "Dinner": dinner,
            "Snack": snack,
        }

        totals = calculate_plan_totals(meals)

        total_calories = totals["total_calories"]
        total_protein = totals["total_protein"]

        # 0 = target reached
        # 1 = target not reached
        #
        # This makes reaching the calorie target more important
        # than simply being mathematically close to it.
        if total_calories >= calorie_target:
            target_group = 0
            calorie_difference = total_calories - calorie_target
        else:
            target_group = 1
            calorie_difference = calorie_target - total_calories

        # High-protein plans prefer more protein when calorie
        # performance is otherwise comparable.
        protein_score = (
            -total_protein
            if goal == "high_protein"
            else 0
        )

        score = (
            target_group,
            calorie_difference,
            protein_score,
        )

        if best_score is None or score < best_score:
            best_score = score

            best_plan = {
                "meals": meals,
                **totals,
            }

    return best_plan


def generate_weekly_plan(recipes, calorie_target, goal):
    """Build a Monday–Sunday plan using the same meals each day."""

    daily = generate_daily_plan(
        recipes,
        calorie_target,
        goal,
    )

    weekly = {}

    for day in WEEKDAYS:
        weekly[day] = deepcopy(daily)

    return weekly