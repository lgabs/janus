  
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

This is the most simple approach to analyze your A/B Test. Just input the information and wait for calculations.

Page in construction.
"""
)

