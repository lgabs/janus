from typing import Any, Dict, Iterator, List, Optional, Text
import numpy as np
from scipy.stats import beta


class Distribution:
    def sample(self) -> np.ndarray:
        raise NotImplementedError(
            "An Distribution must implement a sampler for its own distribution"
        )

    def update(self):
        raise NotImplementedError(
            "An Distribution must implement a update method for posterior calculations"
        )

    def chance_to_beat(
        self,
        sample_metrics_for_variant_of_interest: np.ndarray,
        sample_metrics_for_other_variant: np.ndarray,
        sample_size: int,
    ) -> float:
        """
        In this method, it is assumed that one wants to know the probability that the metric on
        variant of interest (conversion, revenue, ARPU etc) is higher than other variant's metric, so pay attention to the order of arguments.
        This is the Monte Carlo implementation for Definition 6.1 on VWO paper.
        """
        return (
            sum(
                sample_metrics_for_variant_of_interest
                > sample_metrics_for_other_variant
            )
            / sample_size
        )

    def expected_loss(
        self,
        sample_metrics_for_variant_of_interest: np.ndarray,
        sample_metrics_for_other_variant: np.ndarray,
        sample_size: int,
    ) -> float:
        """
        In this method, it is assumed that one wants to know the expected loss for the metric on
        variant of interest (conversion, revenue, ARPU etc) compared to the other variant's metric, so pay attention to the order of arguments.
        This is the Monte Carlo implementation for Definition 6.1 on VWO paper.
        """

        diff = sample_metrics_for_other_variant - sample_metrics_for_variant_of_interest

        return sum(diff * (diff > 0)) / sample_size


class ConversionDistribution(Distribution):
    """
    Class to handle Converstion Rate (Lambda) posterior calculations and sampling.
    """

    def __init__(self, a=1, b=1):
        self.a = a
        self.b = b

    def sample(self, sample_size: int) -> np.ndarray:
        return np.random.beta(a=self.a, b=self.b, size=sample_size)

    def update(self, paids: int, not_paids: int):
        self.a += paids
        self.b += not_paids


class RevenueDistribution(Distribution):
    """
    Class to handle Revenue (theta) posterior calculations and sampling.
    """

    def __init__(self, k=1, theta=1):
        self.k = k
        self.theta = theta

    def sample(self, sample_size: int) -> np.ndarray:
        return np.random.gamma(shape=self.k, scale=self.theta, size=sample_size)

    def update(self, paids: int, revenue: float):
        self.k += paids
        self.theta = 1 / (1 + revenue)


class ARPUDistribution(Distribution):
    """
    Class to handle ARPU (theta) posterior calculations and sampling.
    We do not need any implementation, because the calculation uses
    both Conversion and Revenue's Distributions.
    """

    def __init__(self):
        pass

    def sample(self, sample_size: int) -> np.ndarray:
        pass

    def update(self, paids: int, revenue: float):
        pass
