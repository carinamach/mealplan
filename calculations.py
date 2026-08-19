"""Simple estimate calculations, kept separate from Flask routes."""

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.4,
    "light": 1.55,
    "moderate": 1.7,
    "active": 1.9,
}

GOAL_ADJUSTMENTS = {
    "lose_weight": -400,
    "maintain_weight": 0,
    "low_calorie": -250,
    "high_protein": 0,
}

SEX_CONSTANTS = {
    "female": -161,
    "male": 5,
    "prefer_not_to_say": -78,
}


def calculate_targets(age, height, weight, activity_level, goal, biological_sex):
    """Return simple daily calorie and protein estimates.

    This is intentionally a rough project estimate, not medical advice.
    """
    if activity_level not in ACTIVITY_MULTIPLIERS:
        raise ValueError("Choose a valid activity level.")
    if goal not in GOAL_ADJUSTMENTS:
        raise ValueError("Choose a valid goal.")
    if biological_sex not in SEX_CONSTANTS:
        raise ValueError("Choose a valid option for biological sex.")

    # A simple starting estimate using age, height (cm), weight (kg), and sex.
    # "Prefer not to say" uses the midpoint of the female and male constants.
    base_calories = (10 * weight) + (6.25 * height) - (5 * age) + SEX_CONSTANTS[biological_sex]
    maintenance_calories = base_calories * ACTIVITY_MULTIPLIERS[activity_level]
    calorie_target = round(maintenance_calories + GOAL_ADJUSTMENTS[goal])

    # The high-protein option uses a higher, simple target per kilogram of body weight.
    protein_per_kg = 1.6 if goal == "high_protein" else 0.83
    protein_target = round(weight * protein_per_kg)
    height_in_metres = height / 100
    bmi = round(weight / (height_in_metres**2), 1)

    return {
        "calories": calorie_target,
        "protein": protein_target,
        "bmi": bmi,
    }
