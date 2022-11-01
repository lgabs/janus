# Databricks notebook source
# COMMAND ----------

from typing import Any, Dict, Iterator, List, Optional, Text
from janus.stats.constants import MAX_ROUND_DIGITS, SAMPLE_SIZE, BOOSTRAP_SAMPLES
from janus.stats.metrics import (
    Distribution,
    ConversionDistribution,
    RevenueDistribution,
    ARPUDistribution,
)
from janus.stats.pyspark_bootstraping import (
    get_bootstraped_mean,
    get_parallel_bootstrap,
)
import numpy as np
import pandas as pd
import logging


class Variant:
    """
    Store variant relevant information and methods to consolidate data.
    Variant is synonym of alternative.
    """

    def __init__(self, name: str):
        self.name = name
        self.distributions = {}
        self.statistics = {}

    def consolidate_results(self, df: pd.DataFrame):
        """
        Store resume metrics for later statistic calculations over a input dataframe that contains the
        situation of each impression made on users
        """

        variant_df = df.query(f"alternative == '{self.name}'")

        self.variant_df = variant_df
        self.users = variant_df.shape[0]
        self.sales = variant_df["sales"].sum()
        self.paids = variant_df["sales"].sum()
        self.revenue = variant_df["revenue"].sum()
        self.conversion = (
            round(self.paids / self.users, MAX_ROUND_DIGITS) if self.users > 0 else 0
        )
        self.ticket = (
            round(self.revenue / self.paids, MAX_ROUND_DIGITS) if self.paids > 0 else 0
        )
        self.arpu = (
            round(self.revenue / self.users, MAX_ROUND_DIGITS) if self.users > 0 else 0
        )

    def calculate_conversion(self):
        # get prior distribution for conversion and update it with results
        conversion_distribution = ConversionDistribution()
        not_paids = self.users - self.paids
        conversion_distribution.update(self.paids, not_paids)

        # sample values for conversion from the posterior distribution
        self.conversion_sampling = conversion_distribution.sample(SAMPLE_SIZE)
        self.distributions["conversion"] = conversion_distribution
        self.statistics["conversion"] = {}

    def calculate_revenue(self):
        # get prior distribution for revenue and update it with results
        revenue_distribution = RevenueDistribution()
        revenue_distribution.update(self.paids, self.revenue)

        # sample values for revenue from the posterior distribution
        self.revenue_sampling = revenue_distribution.sample(SAMPLE_SIZE)
        self.distributions["revenue"] = revenue_distribution
        self.statistics["revenue"] = {}

    def calculate_arpu(self):
        # get prior distribution for ARPU and update it with results
        arpu_distribution = ARPUDistribution()

        # sample values for ARPU from the posterior distribution (not necessary since its been calculated already)
        self.arpu_sampling = self.conversion_sampling / self.revenue_sampling
        self.distributions["arpu"] = arpu_distribution
        self.statistics["arpu"] = {}

    def calculate_probabilities(self, other_variant, metric_name: str):
        distribution = self.distributions[metric_name]
        self_metric_samples = getattr(self, metric_name + "_sampling")
        other_variant_metric_samples = getattr(other_variant, metric_name + "_sampling")

        if metric_name == "revenue":
            # for revenue, we shall compare 1/theta's
            self_metric_samples = 1 / self_metric_samples
            other_variant_metric_samples = 1 / other_variant_metric_samples

        # calculate chance to beat the other variant
        self.statistics[metric_name]["chance_to_beat"] = distribution.chance_to_beat(
            self_metric_samples, other_variant_metric_samples, SAMPLE_SIZE
        )

        # calculate expected loss for the variant compared to the other
        self.statistics[metric_name]["expected_loss"] = distribution.expected_loss(
            self_metric_samples, other_variant_metric_samples, SAMPLE_SIZE
        )

    def calculate_bootstrap(
        self, metric_name: str, eval_function=get_bootstraped_mean, spark_session=None
    ):

        if metric_name == "revenue":
            data = list(self.variant_df.query("sales == 1")["revenue"])
        elif metric_name == "conversion":
            data = list(self.variant_df["sales"])
        elif metric_name == "arpu":
            data = list(self.variant_df["revenue"])

        self.statistics[metric_name]["bootstrapped_mean"] = get_parallel_bootstrap(
            eval_function, data, BOOSTRAP_SAMPLES, spark_session
        )


class Experiment:
    """
    Class to handle an experiment containing two variants.
    """

    def __init__(
        self,
        name: str,
        keymetrics: List[str],
        baseline_variant_name: str = "baseline",
        do_boostrap=False,
        spark_session=None,
    ):
        self.name = name
        self.keymetrics = keymetrics
        self.baseline_variant_name = baseline_variant_name
        self.do_boostrap = do_boostrap
        if do_boostrap and not spark_session:
            raise Exception(
                "A spark session is necessary to run bootstrap calculations."
            )
        self.spark_session = spark_session
        self.results = {}

    def run_experiment(self, df_results_per_user: pd.DataFrame):

        logging.info(f"INITIALIZING experiment '{self.name}' evaluation...")
        variant_names = list(df_results_per_user.alternative.unique())
        assert (
            len(variant_names) == 2
        ), "experiment does not have exactly two variants as expected."
        assert (
            self.baseline_variant_name in variant_names
        ), "baseline variant name informed is not present on experiment data."
        treatment_variant_name = [
            c for c in variant_names if c != self.baseline_variant_name
        ][0]

        # Build variants and consolidate user data over them
        logging.info("consolidating metrics over variants...")
        variantA = Variant(name=self.baseline_variant_name)
        variantB = Variant(name=treatment_variant_name)
        self.variants = [variantA, variantB]

        variantA.consolidate_results(df_results_per_user)
        variantB.consolidate_results(df_results_per_user)

        # Extract Bayesian Statistics for each metric and boostrap if necessary
        for metric_name in self.keymetrics:
            logging.info(
                f"calculating bayesian statistics over variants for metric {metric_name}"
            )
            self.evaluate_statistics(variantA, variantB, metric_name)

        logging.info("consolidating final results...")
        self.consolidate_results(variantA, variantB)

        logging.info("FINISHED experiment evaluation.")

        return self.results

    def evaluate_statistics(
        self, variantA: Variant, variantB: Variant, metric_name: str
    ):
        for variant in [variantA, variantB]:
            logging.info(f"sampling data for variant {variant.name}...")
            if metric_name == "conversion":
                variant.calculate_conversion()
            if metric_name == "revenue":
                variant.calculate_revenue()
            if metric_name == "arpu":
                variant.calculate_arpu()

            if self.do_boostrap:
                variant.calculate_boostrap(metric_name)

        for variant1, variant2 in zip((variantA, variantB), (variantB, variantA)):
            logging.info(
                f"calculating probability to beat and expected loss for variant {variant1.name}..."
            )
            variant1.calculate_probabilities(variant2, metric_name)

    def consolidate_results(self, variantA: Variant, variantB: Variant):

        for variant_interest, variant_other in zip(
            (variantA, variantB), (variantB, variantA)
        ):
            logging.info(
                f"consolidating final results for variant {variant_interest.name}..."
            )
            results = {}
            metrics_list = [
                "users",
                "sales",
                "paids",
                "revenue",
                "conversion",
                "ticket",
                "arpu",
                "statistics",
            ]
            for metric in metrics_list:
                results[metric] = getattr(variant_interest, metric)

            results["ratio"] = variant_interest.users / (
                variant_interest.users + variant_other.users
            )
            for metric in self.keymetrics:
                results["statistics"][metric]["lift"] = get_lift(
                    getattr(variant_interest, metric), getattr(variant_other, metric)
                )
                results["statistics"][metric]["diff"] = getattr(
                    variant_interest, metric
                ) - getattr(variant_other, metric)

            self.results[variant_interest.name] = results


def get_lift(a: float, b: float) -> float:
    if a > 0:
        return a / b - 1
    else:
        return 0.0
