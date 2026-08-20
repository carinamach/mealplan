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


def build_weekly_shopping_list(weekly_plan):
    """Build a combined shopping list from a weekly plan.

    Each planned meal is counted as one serving by default. If a recipe's
    `servings` value is greater than 1, ingredient amounts are scaled so that
    one planned meal corresponds to `1 / servings` of the recipe's ingredient
    quantities. The function returns the grouped list and the total number of
    planned portions in the week.
    """
    combined = {}
    portions = 0

    for day_plan in weekly_plan.values():
        meals = day_plan.get("meals", {})
        for recipe in meals.values():
            if not recipe:
                continue

            portions += 1
            recipe_servings = recipe.get("servings", 1) or 1
            # Each planned meal represents one desired portion.
            multiplier = 1.0 / recipe_servings

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

    return [(category, items) for category, items in grouped.items() if items], portions

    grouped = {category: [] for category in CATEGORY_ORDER}
    for item in sorted(combined.values(), key=lambda item: item["name"].casefold()):
        item["amount"] = format_amount(item["amount"])
        grouped[categorize_ingredient(item["name"])].append(item)

    return [(category, items) for category, items in grouped.items() if items]
