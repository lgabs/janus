import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats
from scipy.stats import norm
import altair as alt

import janus
from janus.stats.experiment import Experiment, Variant

from utils import save_results_in_session_state

import logging

logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="A/B Testing App", page_icon="📊"
)

st.sidebar.markdown("# Main Page")

st.markdown(
    """
# 📊 A/B Testing App

This is a tool to automate your decisions in an A/B Test Experiment with two alternatives, where 
you want to know which one is better¹. It is focused on conversion and revenue evaluation, typical in e-commerce.

## How to use

There are two ways of using: using a CSV with one participant per row or a CSV with summary results per day, week or any period. Choose which page you want in the lateral bar.

¹ To analyze more than one alternative, you can approximately compare 
them two by two, but avoid this with more than 3. We're working on this feature in the roadmap.

""")
