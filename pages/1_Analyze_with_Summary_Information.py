  
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

st.set_page_config(
    page_title=" A/B Testing using summary information", page_icon="📊"
)

st.markdown(
    """
# 📊 A/B Testing using Summary Information

**[Page in construction]**

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
    control_value = st.number_input(
        label="Total Conversion Value in Control",
        value=200,
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
    test_value = st.number_input(
        label="Total Conversion Value in Treatment",
        value=250,
    )

    submit_button = st.form_submit_button(label="Run Experiment")

