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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

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
        if show:
            print(
                pd.DataFrame(self.conversion_results).to_markdown(
                    tablefmt="grid", index=False
                )
            )

    def run_arpu_experiment(self, sim_count: int = 100_000, show=False):
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

        return _df_summary, _df_conv, _df_arpu, _df_rev_per_sale


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
        df_summary, df_conv, df_arpu, df_rev_per_sale = experiment.get_reports()

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
        }
    except Exception as e:
        error_msg = f"Error in experiment analysis: {str(e)}"
        stack_trace = traceback.format_exc()
        logger.error(f"{error_msg}\n{stack_trace}")
        raise HTTPException(status_code=400, detail=error_msg)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
