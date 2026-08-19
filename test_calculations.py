import unittest

from calculations import calculate_targets


class CalculationTests(unittest.TestCase):
    def test_high_protein_goal_uses_higher_protein_target(self):
        standard = calculate_targets(30, 170, 70, "moderate", "maintain_weight", "female")
        high_protein = calculate_targets(30, 170, 70, "moderate", "high_protein", "female")

        self.assertGreater(high_protein["protein"], standard["protein"])
        self.assertEqual(high_protein["calories"], standard["calories"])

    def test_bmi_uses_weight_and_height(self):
        targets = calculate_targets(30, 170, 70, "moderate", "maintain_weight", "female")

        self.assertEqual(targets["bmi"], 24.2)

    def test_prefer_not_to_say_uses_middle_calorie_estimate(self):
        female = calculate_targets(30, 170, 70, "moderate", "maintain_weight", "female")
        middle = calculate_targets(30, 170, 70, "moderate", "maintain_weight", "prefer_not_to_say")
        male = calculate_targets(30, 170, 70, "moderate", "maintain_weight", "male")

        self.assertLess(female["calories"], middle["calories"])
        self.assertLess(middle["calories"], male["calories"])


if __name__ == "__main__":
    unittest.main()
