from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
import pandas as pd
from bayesian_testing.experiments import (
    BinaryDataTest,
    DeltaLognormalDataTest,
    ExponentialDataTest,
)
from dataclasses import dataclass
import json
import os
import logging
import traceback
from datetime import datetime
from scipy import stats

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.info(f"Starting application with log level: {log_level}")

# Create directories if they don't exist
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app = FastAPI(title="Janus: Bayesian A/B Testing App")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")


@dataclass
class Variant:
    name: str
    impressions: int
    conversions: int
    revenue: float


class WebsiteExperiment:
    """
    Class to run website experiments from aggregated data.
    Focused in conversion, revenue and ARPU metrics.
    """

    def __init__(self, variants: List[Variant], baseline_variant: str):
        self.variants: List[Variant] = variants
        self.variants_results = []
        self.baseline_variant: str = baseline_variant

    def run_conversion_experiment(self, sim_count: int = 100_000, show=False):
        self.conversion_test: BinaryDataTest = BinaryDataTest()
        for v in self.variants:
            self.conversion_test.add_variant_data_agg(
                v.name, totals=v.impressions, positives=v.conversions
            )

        self.conversion_results = self.conversion_test.evaluate()
        # Create the posterior distributions for conversion rates
        # For binary data, the posterior is a Beta distribution with parameters:
        # alpha = a_prior + positives, beta = b_prior + (totals - positives)
        self.conversion_distributions = {}
        for variant_name, variant_data in zip(
            self.conversion_test.variant_names, self.conversion_results
        ):
            a_prior = 0.5  # Default prior in BinaryDataTest
            b_prior = 0.5  # Default prior in BinaryDataTest
            alpha = a_prior + variant_data["positives"]
            beta = b_prior + (variant_data["totals"] - variant_data["positives"])
            # Create a Beta distribution with these parameters
            self.conversion_distributions[variant_name] = stats.beta(alpha, beta)

        if show:
            print(
                pd.DataFrame(self.conversion_results).to_markdown(
                    tablefmt="grid", index=False
                )
            )

    def run_arpu_experiment(self, sim_count: int = 100_000, show=False):
        self.arpu_test: DeltaLognormalDataTest = DeltaLognormalDataTest()
        for v in self.variants:
            rev_logs = (
                [np.log(v.revenue / v.conversions)] * v.conversions
                if v.conversions > 0
                else []
            )
            self.arpu_test.add_variant_data_agg(
                v.name,
                totals=v.impressions,
                positives=v.conversions,
                sum_values=v.revenue,
                sum_logs=sum(rev_logs) if rev_logs else 0,
                sum_logs_2=sum([np.square(l) for l in rev_logs]) if rev_logs else 0,
            )

        self.arpu_results = self.arpu_test.evaluate()

        # Create the posterior distributions for ARPU
        # For delta-lognormal data, we need to simulate from the model
        self.arpu_distributions = {}

        # Generate samples for each variant using the DeltaLognormalDataTest model
        # We'll use the eval_simulation method which returns probabilities and expected loss
        pbbs, loss = self.arpu_test.eval_simulation(sim_count=1000, seed=42)

        # For each variant, we'll generate samples from the posterior distribution
        for variant_name in self.arpu_test.variant_names:
            variant_idx = self.arpu_test.variant_names.index(variant_name)

            # Get the parameters for this variant
            totals = self.arpu_test.totals[variant_idx]
            positives = self.arpu_test.positives[variant_idx]
            sum_logs = self.arpu_test.sum_logs[variant_idx]
            sum_logs_2 = self.arpu_test.sum_logs_2[variant_idx]

            # Get the priors
            a_prior_beta = self.arpu_test.a_priors_beta[variant_idx]
            b_prior_beta = self.arpu_test.b_priors_beta[variant_idx]
            m_prior = self.arpu_test.m_priors[variant_idx]
            a_prior_ig = self.arpu_test.a_priors_ig[variant_idx]
            b_prior_ig = self.arpu_test.b_priors_ig[variant_idx]
            w_prior = self.arpu_test.w_priors[variant_idx]

            # Generate samples from the posterior distribution
            # First, sample from the Beta distribution for conversion rate
            np.random.seed(42 + variant_idx)  # Different seed for each variant
            conversion_rate = stats.beta(
                a_prior_beta + positives, b_prior_beta + (totals - positives)
            ).rvs(size=1000)

            # For positive values, we need to sample from the log-normal distribution
            # The parameters for the log-normal are derived from the data
            if positives > 0:
                # Calculate posterior parameters for the log-normal distribution
                n = positives
                w_n = w_prior + n
                m_n = (w_prior * m_prior + sum_logs) / w_n
                a_n = a_prior_ig + n / 2
                b_n = b_prior_ig + 0.5 * (
                    sum_logs_2 - 2 * m_n * sum_logs + w_n * m_n**2
                )

                # Sample from the inverse gamma for variance
                np.random.seed(42 + variant_idx + 100)  # Different seed
                variance = stats.invgamma(a_n, scale=b_n).rvs(size=1000)

                # Sample from the normal for mean
                np.random.seed(42 + variant_idx + 200)  # Different seed
                mean = stats.norm(m_n, np.sqrt(variance / w_n)).rvs(size=1000)

                # Now sample from the log-normal with these parameters
                np.random.seed(42 + variant_idx + 300)  # Different seed
                log_normal_samples = np.exp(
                    stats.norm(mean, np.sqrt(variance)).rvs(size=1000)
                )

                # Combine with conversion rate to get ARPU
                arpu_samples = conversion_rate * log_normal_samples
            else:
                # If no conversions, ARPU is 0
                arpu_samples = np.zeros(1000)

            # Store the samples
            self.arpu_distributions[variant_name] = arpu_samples.tolist()

        if show:
            print(
                pd.DataFrame(self.arpu_results).to_markdown(
                    tablefmt="grid", index=False
                )
            )

    def run_revenue_per_sale_experiment(self, sim_count: int = 100_000, show=False):
        self.revenue_per_sale_test: ExponentialDataTest = ExponentialDataTest()
        for v in self.variants:
            if v.conversions > 0:
                # For revenue per sale, we use the average revenue per conversion
                # as the scale parameter for the exponential distribution
                avg_revenue_per_sale = v.revenue / v.conversions
                self.revenue_per_sale_test.add_variant_data_agg(
                    v.name, totals=v.conversions, sum_values=v.revenue
                )
            else:
                # Handle the case where there are no conversions
                self.revenue_per_sale_test.add_variant_data_agg(
                    v.name, totals=0, sum_values=0
                )

        # Higher revenue per sale is better, so min_is_best=False
        self.revenue_per_sale_results = self.revenue_per_sale_test.evaluate(
            sim_count=sim_count
        )
        if show:
            print(
                pd.DataFrame(self.revenue_per_sale_results).to_markdown(
                    tablefmt="grid", index=False
                )
            )

    def run(self, **kargs):
        self.run_conversion_experiment(**kargs)
        self.run_arpu_experiment(**kargs)
        self.run_revenue_per_sale_experiment(**kargs)

    def compile_full_data(
        self,
        show: bool = False,
        revenue_precision: int = 4,
        conversion_precision: int = 4,
        probs_precision: int = 4,
    ):
        compiled_res = []
        for v, conv_res, arpu_res, rev_per_sale_res in zip(
            self.variants,
            self.conversion_results,
            self.arpu_results,
            self.revenue_per_sale_results,
        ):
            res = {}
            # header info
            res.update({"variant": v.name})
            res.update(
                {
                    "summary": {
                        "impressions": int(v.impressions),
                        "conversions": int(v.conversions),
                        "revenue": round(v.revenue, revenue_precision),
                        "conversion": round(v.conversions / v.impressions, 4),
                        "avg_ticket": (
                            round(v.revenue / v.conversions, 4)
                            if v.conversions > 0
                            else 0
                        ),
                        "arpu": round(v.revenue / v.impressions, 4),
                    }
                }
            )
            # conversion results
            res.update(
                {
                    "conversion": {
                        "expected_loss": round(conv_res["expected_loss"], 4),
                        "prob_being_best": round(
                            conv_res["prob_being_best"], probs_precision
                        ),
                    }
                }
            )
            # arpu results
            res.update(
                {
                    "arpu": {
                        "expected_loss": round(arpu_res["expected_loss"], 4),
                        "prob_being_best": round(
                            arpu_res["prob_being_best"], probs_precision
                        ),
                    }
                }
            )
            # revenue per sale results
            res.update(
                {
                    "revenue_per_sale": {
                        "expected_loss": round(rev_per_sale_res["expected_loss"], 4),
                        "prob_being_best": round(
                            rev_per_sale_res["prob_being_best"], probs_precision
                        ),
                    }
                }
            )
            compiled_res.append(res)

        self.compiled_res = compiled_res
        return compiled_res

    def get_reports(self, probs_precision: int = 4):
        self.compile_full_data()

        # Debug: Print the structure of revenue_per_sale_results
        print(
            "Revenue per sale results structure:",
            (
                self.revenue_per_sale_results[0]
                if self.revenue_per_sale_results
                else "No results"
            ),
        )

        summaries = []
        conv_stats = []
        arpu_stats = []
        rev_per_sale_stats = []
        baseline_res = [
            res
            for res in self.compiled_res
            if res.get("variant") == self.baseline_variant
        ][0]
        for variant in self.compiled_res:
            summary = {"variant": variant.get("variant")}
            summary.update(variant.get("summary"))
            summaries.append(summary)

            conv = {"variant": variant.get("variant")}
            conv.update(variant.get("conversion"))

            # Find the posterior_mean from the conversion_results
            for result in self.conversion_results:
                if result["variant"] == variant.get("variant"):
                    conv.update({"posterior_mean": result["posterior_mean"]})
                    break

            conv.update(
                {
                    "lift": round(
                        summary["conversion"]
                        / baseline_res.get("summary").get("conversion")
                        - 1,
                        probs_precision,
                    )
                }
            )
            conv_stats.append(conv)

            arpu = {"variant": variant.get("variant")}
            arpu.update(variant.get("arpu"))

            # Find the posterior_mean for ARPU from the arpu_results
            for result in self.arpu_results:
                if result["variant"] == variant.get("variant"):
                    arpu.update({"posterior_mean": result["avg_values"]})
                    break

            arpu.update(
                {
                    "lift": round(
                        summary["arpu"] / baseline_res.get("summary").get("arpu") - 1,
                        probs_precision,
                    )
                }
            )
            arpu_stats.append(arpu)

            rev_per_sale = {"variant": variant.get("variant")}
            rev_per_sale.update(variant.get("revenue_per_sale"))

            # Find the posterior_mean for revenue per sale from the revenue_per_sale_results
            for result in self.revenue_per_sale_results:
                if result["variant"] == variant.get("variant"):
                    rev_per_sale.update({"posterior_mean": result["posterior_mean"]})
                    break

            baseline_avg_ticket = baseline_res.get("summary").get("avg_ticket")
            variant_avg_ticket = summary["avg_ticket"]
            # Handle division by zero
            if baseline_avg_ticket > 0 and variant_avg_ticket > 0:
                rev_per_sale.update(
                    {
                        "lift": round(
                            variant_avg_ticket / baseline_avg_ticket - 1,
                            probs_precision,
                        )
                    }
                )
            else:
                rev_per_sale.update({"lift": 0})
            rev_per_sale_stats.append(rev_per_sale)

        _df_summary = pd.DataFrame(summaries)
        _df_conv = pd.DataFrame(conv_stats)
        _df_arpu = pd.DataFrame(arpu_stats)
        _df_rev_per_sale = pd.DataFrame(rev_per_sale_stats)

        # Get conversion distributions
        conversion_distributions = {}
        for variant_name, distribution in self.conversion_distributions.items():
            # Sample 500 points from the distribution for visualization
            # Using a fixed random seed for reproducibility
            np.random.seed(42)
            conversion_distributions[variant_name] = distribution.rvs(
                size=1000
            ).tolist()

        # Get ARPU distributions
        arpu_distributions = self.arpu_distributions

        # Get revenue per sale distributions
        # For exponential data, the posterior is a Gamma distribution with parameters:
        # alpha = a_prior + totals, beta = b_prior + sum_values
        revenue_per_sale_distributions = {}
        for variant_name, variant_data in zip(
            self.revenue_per_sale_test.variant_names, self.revenue_per_sale_results
        ):
            # Get the parameters for the Gamma distribution
            # In ExponentialDataTest, the prior is Gamma(1, 0)
            a_prior = 1  # Default prior in ExponentialDataTest
            b_prior = 0  # Default prior in ExponentialDataTest

            # Get the data for this variant
            totals = variant_data["totals"]
            sum_values = variant_data["sum_values"]

            # Calculate the parameters for the posterior Gamma distribution
            alpha = a_prior + totals
            beta = b_prior + sum_values

            # Create samples from the Gamma distribution
            np.random.seed(
                42 + self.revenue_per_sale_test.variant_names.index(variant_name)
            )
            if totals > 0:  # Only generate samples if there are conversions
                revenue_per_sale_distributions[variant_name] = (
                    stats.gamma(alpha, scale=1 / beta if beta > 0 else 1)
                    .rvs(size=1000)
                    .tolist()
                )
            else:
                # If no conversions, use a default distribution
                revenue_per_sale_distributions[variant_name] = np.zeros(1000).tolist()

        return (
            _df_summary,
            _df_conv,
            _df_arpu,
            _df_rev_per_sale,
            conversion_distributions,
            arpu_distributions,
            revenue_per_sale_distributions,
        )


# Pydantic models for API
class VariantInput(BaseModel):
    name: str
    impressions: int
    conversions: int
    revenue: float


class ExperimentInput(BaseModel):
    variants: List[VariantInput]
    baseline_variant: str


class ExperimentResult(BaseModel):
    summary: dict
    conversion_stats: dict
    arpu_stats: dict


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/analyze")
async def analyze_experiment(experiment_input: ExperimentInput):
    logger.info(
        f"Received experiment analysis request with {len(experiment_input.variants)} variants"
    )
    try:
        # Log input data summary
        logger.info(f"Baseline variant: {experiment_input.baseline_variant}")
        for v in experiment_input.variants:
            logger.info(
                f"Variant {v.name}: impressions={v.impressions}, conversions={v.conversions}, revenue={v.revenue}"
            )

        # Convert input to Variant objects
        variants = [
            Variant(
                name=v.name,
                impressions=v.impressions,
                conversions=v.conversions,
                revenue=v.revenue,
            )
            for v in experiment_input.variants
        ]

        # Create and run experiment
        logger.info("Creating experiment and running analysis")
        experiment = WebsiteExperiment(variants, experiment_input.baseline_variant)
        experiment.run()

        # Get reports
        logger.info("Generating experiment reports")
        (
            df_summary,
            df_conv,
            df_arpu,
            df_rev_per_sale,
            conversion_distributions,
            arpu_distributions,
            revenue_per_sale_distributions,
        ) = experiment.get_reports()

        # Convert DataFrames to dictionaries
        summary_dict = df_summary.to_dict(orient="records")
        conv_dict = df_conv.to_dict(orient="records")
        arpu_dict = df_arpu.to_dict(orient="records")
        rev_per_sale_dict = df_rev_per_sale.to_dict(orient="records")

        logger.info("Successfully completed experiment analysis")
        return {
            "summary": summary_dict,
            "conversion_stats": conv_dict,
            "arpu_stats": arpu_dict,
            "revenue_per_sale_stats": rev_per_sale_dict,
            "conversion_distributions": conversion_distributions,
            "arpu_distributions": arpu_distributions,
            "revenue_per_sale_distributions": revenue_per_sale_distributions,
        }
    except Exception as e:
        error_msg = f"Error in experiment analysis: {str(e)}"
        stack_trace = traceback.format_exc()
        logger.error(f"{error_msg}\n{stack_trace}")

        # Log more details about the input data for debugging
        logger.error(f"Input data that caused the error: {experiment_input.dict()}")

        # Return more detailed error information
        raise HTTPException(
            status_code=400,
            detail={
                "error": error_msg,
                "traceback": stack_trace,
                "input_data": experiment_input.dict(),
            },
        )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
