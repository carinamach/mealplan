"""Build a simple categorized shopping list from a meal plan."""

CATEGORY_ORDER = ("Meat & fish", "Vegetables", "Fruit", "Dairy", "Pantry")

INGREDIENT_CATEGORIES = {
    "canned tuna": "Meat & fish",
    "chicken breast": "Meat & fish",
    "cod fillet": "Meat & fish",
    "ground turkey": "Meat & fish",
    "lean beef strips": "Meat & fish",
    "shrimp": "Meat & fish",
    "smoked salmon": "Meat & fish",
    "avocado": "Vegetables",
    "basil": "Vegetables",
    "bell pepper": "Vegetables",
    "broccoli": "Vegetables",
    "carrot": "Vegetables",
    "carrots": "Vegetables",
    "cherry tomatoes": "Vegetables",
    "corn": "Vegetables",
    "cucumber": "Vegetables",
    "edamame": "Vegetables",
    "garlic": "Vegetables",
    "lettuce": "Vegetables",
    "mixed vegetables": "Vegetables",
    "potatoes": "Vegetables",
    "spinach": "Vegetables",
    "stir-fry vegetables": "Vegetables",
    "sweet potato": "Vegetables",
    "tomato": "Vegetables",
    "zucchini": "Vegetables",
    "apple": "Fruit",
    "banana": "Fruit",
    "mixed berries": "Fruit",
    "cottage cheese": "Dairy",
    "cream cheese": "Dairy",
    "eggs": "Dairy",
    "feta cheese": "Dairy",
    "Greek yogurt": "Dairy",
    "light cream": "Dairy",
    "milk": "Dairy",
    "mozzarella": "Dairy",
    "parmesan": "Dairy",
}


def categorize_ingredient(name):
    """Return a grocery category for one ingredient name."""
    return INGREDIENT_CATEGORIES.get(name, "Pantry")


def format_amount(amount):
    """Show whole numbers without a decimal place."""
    if float(amount).is_integer():
        return str(int(amount))
    return str(round(amount, 1))


def build_shopping_list(meals, portions=None):
    """Collect, combine, and group ingredients from selected meals.

    `meals` is a mapping of meal_name -> recipe. `portions` is an optional
    dict mapping meal_name -> number_of_portions the user intends to cook for
    that meal; this scales ingredient amounts accordingly. By default each
    meal is treated as one portion.
    """
    portions = portions or {}
    combined = {}

    for meal_name, recipe in meals.items():
        if not recipe:
            continue

        planned = float(portions.get(meal_name, 1) or 1)
        recipe_servings = float(recipe.get("servings", 1) or 1)
        multiplier = planned / recipe_servings

        for ingredient in recipe["ingredients"]:
            name = ingredient["name"]
            unit = ingredient.get("unit") or ""
            key = (name.casefold(), unit.casefold())

            if key not in combined:
                combined[key] = {"name": name, "unit": unit, "amount": 0}

            combined[key]["amount"] += ingredient["amount"] * multiplier

    grouped = {category: [] for category in CATEGORY_ORDER}
    for item in sorted(combined.values(), key=lambda item: item["name"].casefold()):
        item["amount"] = format_amount(item["amount"])
        grouped[categorize_ingredient(item["name"])].append(item)

    return [(category, items) for category, items in grouped.items() if items]


def build_weekly_shopping_list(weekly_plan, portions_map=None):
    """Build a combined shopping list from a weekly plan.

    `weekly_plan` is a mapping day -> plan. `portions_map` is an optional
    mapping day -> { meal_name: planned_portions } that controls how many
    portions the user intends to cook for each meal. If omitted, each planned
    meal counts as one portion. Ingredient amounts are scaled by
    `planned_portions / recipe.servings` for each occurrence and then summed
    across the week.

    Returns a tuple of (grouped_list, total_planned_portions).
    """
    portions_map = portions_map or {}
    combined = {}
    total_portions = 0

    for day, day_plan in weekly_plan.items():
        meals = day_plan.get("meals", {})
        day_portions = portions_map.get(day, {})

        for meal_name, recipe in meals.items():
            if not recipe:
                continue

            planned = float(day_portions.get(meal_name, 1) or 1)
            total_portions += planned
            recipe_servings = float(recipe.get("servings", 1) or 1)
            multiplier = planned / recipe_servings

            for ingredient in recipe["ingredients"]:
                name = ingredient["name"]
                unit = ingredient.get("unit") or ""
                key = (name.casefold(), unit.casefold())

                if key not in combined:
                    combined[key] = {"name": name, "unit": unit, "amount": 0}

                combined[key]["amount"] += ingredient["amount"] * multiplier

    grouped = {category: [] for category in CATEGORY_ORDER}
    for item in sorted(combined.values(), key=lambda item: item["name"].casefold()):
        item["amount"] = format_amount(item["amount"])
        grouped[categorize_ingredient(item["name"])].append(item)

    return [(category, items) for category, items in grouped.items() if items], int(total_portions)
