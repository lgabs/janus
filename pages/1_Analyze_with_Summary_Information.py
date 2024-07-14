import pandas as pd
import numpy as np
import scipy.stats
from scipy.stats import norm
import streamlit as st

import logging

import janus
from janus.stats.experiment import Experiment, Variant
from janus.utils.make_dataframe_multivariate import (
    create_per_user_dataframe_multivariate,
)

from utils import save_results_in_session_state, explain_metrics, print_warning

st.set_page_config(page_title=" A/B Testing using summary information", page_icon="📊")

print_warning()

st.markdown(
    """
# 📊 A/B Testing using Summary Information

This is the most simple approach to analyze your A/B Test. Just input these summary information and wait for calculations:

- **total impressions in control/treatment**: total of participants in each variant.
- **total conversions in control/treatment**: total of conversions in each variant.
- **total conversion value in control/treatment**: the sum of conversion values in each variant (e.g.: revenue).
"""
)


with st.form(key="my_form"):
    # Control
    control_impressions = st.number_input(
        label="Impressions in Control",
        value=1000,
    )
    control_conversions = st.number_input(
        label="Conversions in Control",
        value=100,
    )
    control_total_value = st.number_input(
        label="Total Conversion Value in Control", value=200.0, step=1.0, format="%.4f"
    )

    # Treatment
    test_impressions = st.number_input(
        label="Impressions in Treatment",
        value=1000,
    )
    test_conversions = st.number_input(
        label="Conversions in Treatment",
        value=120,
    )
    test_total_value = st.number_input(
        label="Total Conversion Value in Treatment",
        value=250.00,
        step=1.0,
        format="%.4f",
    )

    experiment_name = st.text_input(
        label="Experiment Name (Optional)", value="My Experiment"
    )

    submit_button = st.form_submit_button(label="Run Experiment")

if submit_button:
    # create dataframe with summary results
    df = pd.DataFrame(
        data={
            "alternative": ["control", "treatment"],
            "exposure_period": ["2022-01-01"] * 2,  # hacking, not to be used
            "exposures": [control_impressions, test_impressions],
            "conversions": [control_conversions, test_conversions],
            "total_value": [control_total_value, test_total_value],
        }
    )
    conversion_bool_col = "conversions"
    conversion_value_cols = ["total_value"]

    df_per_user_simulated = create_per_user_dataframe_multivariate(
        df, conversion_value_cols=conversion_value_cols
    )

    # st.write("df")
    # st.dataframe(df)
    # st.write("df_per_user_simulated")
    # st.dataframe(df_per_user_simulated)

    # Initialize Experiment
    with st.spinner(f"Analyzing Experiment..."):
        # fix cols names
        # TODO: generalize this code for all pages and generalize
        # lib's revenue col to monetary values
        df_per_user_simulated = df_per_user_simulated.rename(
            columns={"converted": "sales", "total_value": "revenue"}
        )  # hacking, sales are generic conversions in janus lib
        experiment = Experiment(
            name=experiment_name,
            keymetrics=["conversion", "revenue", "arpu"],
            baseline_variant_name="control",
        )
        experiment.run_experiment(df_results_per_user=df_per_user_simulated)
        save_results_in_session_state(
            experiment, control_label="control", treatment_label="treatment"
        )

        # Show Results in dataframe form v0
        st.write("## Summary Results")
        _df = pd.DataFrame.from_dict(experiment.results).drop("statistics").T
        st.dataframe(data=_df)

        st.write("## Statistical Results")
        explain_metrics()

        st.write("### Control")
        st.dataframe(data=pd.DataFrame.from_dict(st.session_state.control_stats))

        st.write("### Treatment")
        st.dataframe(data=pd.DataFrame.from_dict(st.session_state.treatment_stats))
