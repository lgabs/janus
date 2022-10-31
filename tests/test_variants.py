import unittest
import pandas as pd
from janus.stats.experiment import Variant, Experiment, get_lift


class VariantTestCase(unittest.TestCase):
    def test_init(self):
        variant = Variant(name="A")
        self.assertEqual(variant.name, "A")

    def test_consolidate_results(self):

        results_per_user = pd.read_csv("tests/results_per_user.csv")
        variant_results = {
            "A": {
                "users": 6,
                "sales": 3,
                "paids": 3,
                "revenue": 600,
                "conversion": 0.5,
                "ticket": 200,
                "arpu": 100,
            },
            "B": {
                "users": 4,
                "sales": 3,
                "paids": 3,
                "revenue": 720,
                "conversion": 0.75,
                "ticket": 240,
                "arpu": 180,
            },
        }

        for variant_name, true_results in variant_results.items():
            variant = Variant(name=variant_name)
            variant.consolidate_results(df=results_per_user)
            for metric_name, true_value in true_results.items():
                self.assertEqual(
                    getattr(variant, metric_name),
                    true_value,
                    msg=f"Error on {metric_name} value, variant {variant_name}.",
                )


if __name__ == "__main__":
    unittest.main(verbosity=1)
