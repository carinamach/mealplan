"""Simple recipe filters for meal type and dietary preferences."""

MEAL_TYPES = ("breakfast", "lunch", "dinner", "snack")

MEAT_AND_FISH = (
    "chicken",
    "turkey",
    "beef",
    "salmon",
    "tuna",
    "shrimp",
    "cod",
)
DAIRY = (
    "milk",
    "yogurt",
    "cheese",
    "feta",
    "mozzarella",
    "parmesan",
    "cottage",
    "cream cheese",
    "light cream",
)
EGGS_AND_HONEY = ("eggs", "honey")
GLUTEN = (
    "bread",
    "bagel",
    "wheat",
    "tortilla",
    "pasta",
    "spaghetti",
    "oats",
    "granola",
    "cracker",
    "soy sauce",
)
NUTS = ("peanut", "almond", "cashew", "walnut", "hazelnut")


def _ingredient_names(recipe):
    return [ingredient["name"].lower() for ingredient in recipe["ingredients"]]


def _contains(names, keywords, skip_if=()):
    for name in names:
        if any(skip in name for skip in skip_if):
            continue
        if any(keyword in name for keyword in keywords):
            return True
    return False


def matches_dietary_preference(recipe, preference):
    """Return whether one recipe is compatible with one dietary preference."""
    tags = set(recipe.get("tags", []))
    names = _ingredient_names(recipe)

    if preference == "vegetarian":
        return ("vegetarian" in tags or "vegan" in tags) and not _contains(names, MEAT_AND_FISH) and "fish" not in tags

    if preference == "vegan":
        return "vegan" in tags and not _contains(
            names,
            MEAT_AND_FISH + DAIRY + EGGS_AND_HONEY,
            skip_if=("coconut",),
        )

    if preference == "gluten-free":
        return "gluten-free" in tags or not _contains(names, GLUTEN)

    if preference == "dairy-free":
        return ("dairy-free" in tags or "vegan" in tags) and not _contains(names, DAIRY, skip_if=("coconut",))

    if preference == "nut-free":
        return not _contains(names, NUTS)

    return True


def matches_dietary_preferences(recipe, preferences):
    """Return whether a recipe matches every selected dietary preference."""
    return all(matches_dietary_preference(recipe, preference) for preference in preferences)


def matches_search(recipe, query):
    """Return whether a recipe name or ingredient contains the search text."""
    if not query:
        return True

    needle = query.casefold().strip()
    if needle in recipe["name"].casefold():
        return True

    return any(needle in ingredient["name"].casefold() for ingredient in recipe["ingredients"])


def filter_recipes(recipes, meal_type=None, preferences=None, query=None):
    """Filter recipes by meal type, dietary preferences, and search text."""
    filtered = recipes

    if meal_type in MEAL_TYPES:
        filtered = [recipe for recipe in filtered if recipe["meal_type"] == meal_type]

    if preferences:
        filtered = [recipe for recipe in filtered if matches_dietary_preferences(recipe, preferences)]

    if query and query.strip():
        filtered = [recipe for recipe in filtered if matches_search(recipe, query)]

    return filtered
