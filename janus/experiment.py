from typing import List

from bayesian_testing.experiments import BinaryDataTest, DeltaLognormalDataTest

from janus.variant import Variant
from janus.utils import money_format
import pandas as pd
import numpy as np
from pprint import pprint

class WebsiteExperiment:
    """
    Class to run website experiments from aggregated data.
    Focused on conversion, revenue, and ARPU metrics.
    """

    def __init__(self, variants: List[Variant], baseline_variant: str):
        """
        Initialize the WebsiteExperiment with a list of variants and the baseline variant.

        Args:
            variants (List[Variant]): List of variants for the experiment.
            baseline_variant (str): The name of the baseline variant.
        """
        self.variants: List[Variant] = variants
        self.variants_results = []
        self.baseline_variant: str = baseline_variant

    def run_conversion_experiment(self, sim_count: int=100_000, show=False):
        """
        Run the conversion experiment using Bayesian testing.

        Args:
            sim_count (int): Number of simulations to run. Defaults to 100,000.
            show (bool): If True, print the results. Defaults to False.
        """
        self.conversion_test: BinaryDataTest = BinaryDataTest()
        for v in self.variants:
            self.conversion_test.add_variant_data_agg(v.name, totals=v.impressions, positives=v.conversions)

        self.conversion_results = self.conversion_test.evaluate()
        if show:
            print(pd.DataFrame(self.conversion_results).to_markdown(tablefmt="grid", index=False))

    def run_arpu_experiment(self, sim_count: int=100_000, show=False):
        """
        Run the ARPU experiment using Bayesian testing.

        Args:
            sim_count (int): Number of simulations to run. Defaults to 100,000.
            show (bool): If True, print the results. Defaults to False.
        """
        self.arpu_test: DeltaLognormalDataTest = DeltaLognormalDataTest()
        for v in self.variants:
            rev_logs = [np.log(v.revenue / v.conversions)] * v.conversions
            self.arpu_test.add_variant_data_agg(
                v.name, 
                totals=v.impressions, 
                positives=v.conversions,
                sum_values=v.revenue,
                sum_logs=sum(rev_logs),
                sum_logs_2=sum([np.square(l) for l in rev_logs]),
            )

        self.arpu_results = self.arpu_test.evaluate()
        if show:
            print(pd.DataFrame(self.arpu_results).to_markdown(tablefmt="grid", index=False))

    def run(self, **kargs):
        """
        Run both conversion and ARPU experiments.

        Args:
            **kargs: Additional keyword arguments to pass to the experiment methods.
        """
        self.run_conversion_experiment(**kargs)
        self.run_arpu_experiment(**kargs)

    def compile_full_data(self, show: bool=False, revenue_precision: int=4, conversion_precision: int=4, probs_precision: int=4):
        """
        Compile full data for all variants and results.

        Args:
            show (bool): If True, print the compiled results. Defaults to False.
            revenue_precision (int): Decimal precision for revenue-related metrics. Defaults to 4.
            conversion_precision (int): Decimal precision for conversion metrics. Defaults to 4.
            probs_precision (int): Decimal precision for probability metrics. Defaults to 4.
        """
        compiled_res = []
        for v, conv_res, arpu_res in zip(
            self.variants, 
            self.conversion_results, 
            self.arpu_results
        ):
            res = {}
            # header info
            res.update({"variant": v.name})
            res.update({
                "summary": {
                "impressions": int(v.impressions),
                "conversions": int(v.conversions),
                "revenue": round(v.revenue, revenue_precision),
                "conversion": round(v.conversions / v.impressions, conversion_precision), 
                "avg_ticket": round(v.revenue / v.conversions, revenue_precision),
                "arpu": round(v.revenue / v.impressions, revenue_precision),
                }
            })
            # conversion results
            res.update({
                "conversion": {
                "expected_loss": round(conv_res["expected_loss"], conversion_precision),
                "prob_being_best": round(conv_res["prob_being_best"], probs_precision),
                }
            })
            # arpu results
            res.update({
                "arpu": {
                "expected_loss": round(arpu_res["expected_loss"], revenue_precision),
                "prob_being_best": round(arpu_res["prob_being_best"], probs_precision),
                }
            })
            compiled_res.append(res)
        
        self.compiled_res = compiled_res
        if show:
            pprint(compiled_res)

    def get_reports(self, probs_precision: int=4):
        """
        Generate summary, conversion, and ARPU reports.

        Args:
            probs_precision (int): Decimal precision for probability metrics. Defaults to 4.

        Returns:
            tuple: DataFrames containing the summary, conversion stats, and ARPU stats.
        """
        self.compile_full_data()

        summaries = []
        conv_stats = []
        arpu_stats = []
        baseline_res = [res for res in self.compiled_res if res.get("variant") == self.baseline_variant][0]
        for variant in self.compiled_res:
            summary = {"variant": variant.get("variant")}
            summary.update(variant.get("summary"))
            summaries.append(summary)

            conv = {"variant": variant.get("variant")}
            conv.update(variant.get("conversion"))
            conv.update({"lift": round(summary["conversion"] / baseline_res.get("summary").get("conversion") - 1, probs_precision)})
            conv_stats.append(conv)

            arpu = {"variant": variant.get("variant")}
            arpu.update(variant.get("arpu"))
            arpu.update({"lift": round(summary["arpu"] / baseline_res.get("summary").get("arpu") - 1, probs_precision)})
            arpu_stats.append(arpu)

        _df_summary = pd.DataFrame(summaries)
        _df_conv = pd.DataFrame(conv_stats)
        _df_arpu = pd.DataFrame(arpu_stats)

        summary_revenue_cols = ["revenue", "avg_ticket", "arpu"]
        for col in summary_revenue_cols:
            _df_summary[col] = _df_summary[col].apply(money_format)
        _df_arpu["expected_loss"] = _df_arpu["expected_loss"].apply(money_format)

        return _df_summary, _df_conv, _df_arpu

    def print_reports(self):
        """
        Print the summary, conversion stats, and ARPU stats reports.
        """
        _df_summary, _df_conv, _df_arpu = self.get_reports()
        
        xlength = len("-----------------") + 11 * len(self.variants)
        print_header = lambda s: print("-" * int((xlength - len(s))/2) + f" {s} " + "-" * int((xlength - len(s))/2))
        print_header("Summary")
        print(
            _df_summary.set_index("variant").T.to_markdown(
                tablefmt="grid",
                numalign='right', stralign='right', disable_numparse=True
                )
        )
        print_header("Conversion Stats")
        print(
            _df_conv.set_index("variant").T.to_markdown(
                tablefmt="grid",
                numalign='right', stralign='right', disable_numparse=True
                )
        )
        print_header("ARPU Stats")
        print(
            _df_arpu.set_index("variant").T.to_markdown(
                tablefmt="grid",
                numalign='right', stralign='right', disable_numparse=True
                )
        )
