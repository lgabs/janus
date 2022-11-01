  
import pandas as pd
import numpy as np
import scipy.stats
from scipy.stats import norm
import altair as alt
import streamlit as st

import logging

import janus
from janus.stats.experiment import Experiment, Variant
from janus.utils.make_dataframe_multivariate import create_per_user_dataframe_multivariate

from utils import save_results_in_session_state

st.markdown(
    """
# 📊 A/B Testing using summary CSV

This approach uses a CSV with summary results per day, week or any period (see example below in _Use example CSV_). This is suitable for cases
where you only have access to gross results per day/week/periods. With your CSV, we'll simulate a dataset with one row per impression
with results equivalent to your data and the apply our statistical engine.

The CSV must have these at least these columns:
- **alternative (string or integer)**: which alternative the participant got exposured.
- **exposure_period (string):** period (e.g day, week etc)
- **exposures (integer):** how many impressions the alternative had in that period.
- **conversions (integer):** number of conversions
- **value (float):** value from conversions in that period. You can choose it in the form below, so the column name can be different. This can actually be any monetary value from conversions, typically it is _revenue_. But it can be other examples like cost, return etc.
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
    uploaded_file = "examples/dataset_summary.csv"
    ab_default = ["alternative"]

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['exposure_period'] = pd.to_datetime(df.exposure_period)

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

        # choose conversion boolean col
        conversion_bool_col = st.multiselect(
            "Column with boolean indicator of conversions",
            options=[c for c in df.columns if c not in [label_values, 'exposure_period', 'exposures']],
            help="Select which column refers to number of conversions.",
            default="conversions"
        )

        # choose conversion value col
        conversion_value_cols = st.multiselect(
            "Column with value from conversions",
            options=[c for c in df.columns if c not in [label_values, 'sales', 'exposure_period', 'exposures']],
            help="Select which column refers to the value that comes from conversions.",
        )
        
        submit_button = st.form_submit_button(label="Continue")

    if submit_button:
        # Treat dataframe to use in the same engine
        conversion_bool_col = conversion_bool_col[0]
        logging.info(f"conversion_bool_col: {conversion_bool_col}")
        logging.info(f"conversion_value_col: {conversion_value_cols}")

        df = df.rename(columns={
            conversion_bool_col: 'conversions',
            })
        df_per_user_simulated = create_per_user_dataframe_multivariate(df, conversion_value_cols=conversion_value_cols)
        st.markdown("""
            ### Data Simulated per user preview
            We use this form as input to our Statistical Engine.
        """)
        st.dataframe(df_per_user_simulated.head())

        if not label_values:
            st.warning(
                "Please select both an **treatment column** and a **Result column**."
            )
            st.stop()

        # type(uploaded_file) == str, means the example file was used
        name = (
            "dataset_summary.csv" if isinstance(uploaded_file, str) else uploaded_file.name
        )
        experiment_name = name.split(".")[0]

        # Initialize Experiment
        with st.spinner(f"Analyzing Experiment for CSV '{name}'..."):
            # fix cols names
            df_per_user_simulated = df_per_user_simulated.rename(columns={'converted': 'sales'}) # hacking, sales are generic conversions in janus lib
            experiment = Experiment(
                name=experiment_name,
                keymetrics=["conversion", "revenue", "arpu"],
                baseline_variant_name=control,
            )
            experiment.run_experiment(df_results_per_user=df_per_user_simulated)
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