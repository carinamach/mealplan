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


def build_shopping_list(meals):
    """Collect, combine, and group ingredients from selected meals."""
    combined = {}

    for recipe in meals.values():
        if not recipe:
            continue

        for ingredient in recipe["ingredients"]:
            name = ingredient["name"]
            unit = ingredient.get("unit") or ""
            key = (name.casefold(), unit.casefold())

            if key not in combined:
                combined[key] = {"name": name, "unit": unit, "amount": 0}

            combined[key]["amount"] += ingredient["amount"]

    grouped = {category: [] for category in CATEGORY_ORDER}
    for item in sorted(combined.values(), key=lambda item: item["name"].casefold()):
        item["amount"] = format_amount(item["amount"])
        grouped[categorize_ingredient(item["name"])].append(item)

    return [(category, items) for category, items in grouped.items() if items]
