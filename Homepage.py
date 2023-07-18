import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats
from scipy.stats import norm

import janus
from janus.stats.experiment import Experiment, Variant

from utils import save_results_in_session_state

import logging

logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="Janus: The A/B Bayesian Testing App", page_icon="📊")

st.image("logo.png", width=250)

st.markdown(
    """
# 📊 Janus: The Bayesian A/B Test App

_Janus_ (the god of decisions) is a tool to automate your decisions in an A/B Test Experiment with two alternatives, where 
you want to know which one is better¹. It is focused on conversion and revenue evaluation, typical in e-commerce. It uses Bayesian Statistics to achieve faster and more insightful results. 

No sample size is obligatory, since you can get partial results and make decisions, but feel free to estimate it to have an idea.

The engine is more powerful than common online websites becasue it measures statistics for 3 variables at once: 
- conversion rate
- value for conversions (e.g. revenue, cost, time spent on page etc) 
- average value per impression (e.g. Average Revenue per User, Cost Per User etc)

See the 'Why Bayesian' section to undestand more advantages of this approach and several references.

"""
)

st.markdown(
    """
¹ To analyze more than one alternative, you can approximately compare 
them two by two, but avoid this with more than 3. We're working on this feature in the roadmap.
"""
)

st.markdown("""## How to use""")

st.markdown(
    """
There are 3 ways to use, each one comes with default examples to understand:

- Page _Analyze with Summary Information_: most simple use case, you have the summary data for the whole test and want results.
- Page _Analyze with Summary CSV_: you have a CSV with summary information per day/week/etc and want results.
- Page _Analyze with Per Impression CSV_: you have a CSV with  results per impression and want results. This is the best approach of all, if data is available, since we have a better understanding of how sales and revenue is really distributed along the data.
"""
)
