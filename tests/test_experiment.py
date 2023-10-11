import unittest
import pandas as pd
from janus.stats.experiment import Variant, Experiment, get_lift


class ExperimentTestCase(unittest.TestCase):
    def test_init(self):
        args = {
            "name": "my_experiment",
            "keymetrics": ["conversion"],
            "baseline_variant_name": "baseline",
        }

        experiment = Experiment(**args)
        for arg, value in args.items():
            self.assertEqual(value, getattr(experiment, arg))

    def test_run_experiment_one_variant(self):
        args = {
            "name": "my_experiment",
            "keymetrics": ["conversion"],
            "baseline_variant_name": "baseline",
        }
        experiment = Experiment(**args)

        df_results_per_user = pd.read_csv("examples/results_per_user.csv")
        with self.assertRaises(AssertionError):
            experiment.run_experiment(df_results_per_user=df_results_per_user)


if __name__ == "__main__":
    unittest.main(verbosity=1)
