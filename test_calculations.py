import unittest

from calculations import calculate_targets


class CalculationTests(unittest.TestCase):
    def test_high_protein_goal_uses_higher_protein_target(self):
        standard = calculate_targets(30, 170, 70, "moderate", "maintain_weight")
        high_protein = calculate_targets(30, 170, 70, "moderate", "high_protein")

        self.assertGreater(high_protein["protein"], standard["protein"])
        self.assertEqual(high_protein["calories"], standard["calories"])


if __name__ == "__main__":
    unittest.main()
