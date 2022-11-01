  
import pandas as pd
import numpy as np
import scipy.stats
from scipy.stats import norm
import altair as alt
import streamlit as st

import logging

import janus
from janus.stats.experiment import Experiment, Variant

from utils import save_results_in_session_state

st.markdown(
    """
# 📊 A/B Testing using per-participant CSV

This way of analyzing uses a CSV with one participant per row.You can upload your experiment results in CSV format to see with significance which alternative has more probability of being the best.
The CSV should have one row per exposure, e.g., one row per participant user. 

First row must be headers and the next rows must contain these columns:
- **id (string or integer)**: any unique id or unique label.
- **alternative (string or integer)**: which alternative the participant got exposured.
- **revenue (float)**: total quantity value for conversions (e.g.: money).
- **sales (integer)**: how many conversions the participant had (typically 0 or 1).


You can see an example clicking in 'Use example file' below for a demonstration.
"""
)

uploaded_file = st.file_uploader("Upload my CSV", type=".csv")

use_example_file = st.checkbox(
    "Use example CSV", False, help="Use in-built example file to demo the app"
)

ab_default = None


# If CSV is not uploaded and checkbox is filled, use values from the example file
# and pass them down to the next if block
logging.info(f"Using example file: {use_example_file}...")
if use_example_file:
    uploaded_file = "examples/results_per_user.csv"
    ab_default = ["alternative"]

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.markdown("### Data preview")
    st.dataframe(df.head())

    st.markdown("### Select columns for analysis:")
    with st.form(key="my_form"):
        label_values = st.multiselect(
            "Column with alternative labels",
            options=df.columns,
            help="Select which column refers to your A/B testing labels.",
            default=ab_default,
        )[0]
        if label_values:
            logging.info(f"alternatives: {df[label_values].unique()}")
            control = df[label_values].unique()[0]
            treatment = df[label_values].unique()[1]
            decide = st.radio(
                f"Is *{treatment}* group the treatment one?",
                options=["Yes", "No"],
                help="Select yes if this is group B (or the treatment group) from your test.",
            )
            if decide == "No":
                control, treatment = treatment, control
            visitors_a = df[label_values].value_counts()[control]
            visitors_b = df[label_values].value_counts()[treatment]

        submit_button = st.form_submit_button(label="Run Experiment")

    if submit_button:
        logging.info("Running Experiment...")
        if not label_values:
            st.warning(
                "Please select both an **treatment column** and a **Result column**."
            )
            st.stop()

        # type(uploaded_file) == str, means the example file was used
        name = (
            "Website_Results.csv" if isinstance(uploaded_file, str) else uploaded_file.name
        )
        experiment_name = name.split(".")[0]

        # Initialize Experiment
        with st.spinner(f"Analyzing Experiment for CSV '{name}'..."):
            experiment = Experiment(
                name=experiment_name,
                keymetrics=["conversion", "revenue", "arpu"],
                baseline_variant_name=control,
            )
            experiment.run_experiment(df_results_per_user=df)
            save_results_in_session_state(experiment, control_label=control, treatment_label=treatment)

        # Show Results in dataframe form v0
        st.write("## Summary Results")
        _df = pd.DataFrame.from_dict(experiment.results).drop('statistics').T
        st.dataframe(data=_df)

        st.write("## Statistical Results")
        st.write("### Control")
        st.dataframe(data=pd.DataFrame.from_dict(st.session_state.control_stats))

        st.write("### Treatment")
        st.dataframe(data=pd.DataFrame.from_dict(st.session_state.treatment_stats))


