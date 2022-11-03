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
    page_title="A/B Bayesian Testing App", page_icon="📊"
)

st.sidebar.markdown("# Main Page")

st.markdown(
    """
# 📊 Bayesian A/B Test App

This is a tool to automate your decisions in an A/B Test Experiment with two alternatives, where 
you want to know which one is better¹. It is focused on conversion and revenue evaluation, typical in e-commerce. It uses Bayesian Statistics to achieve faster and more insightful results. 

No sample size is obligatory, but it is good to estimate it before running your test to have a feel if you can achieve it approximately.

The engine is more powerful than common online websites becasue it measures statistics for 3 variables: 
- conversion rate
- monetary value for conversions (e.g. revenue) 
- average value per impression (e.g. Average Revenue per User)

These are not usual even in famous tools like [abtestguide](https://abtestguide.com/bayesian/) or their [frequentist approach](https://abtestguide.com/calc/), because they only measures for conversion rate.

¹ To analyze more than one alternative, you can approximately compare 
them two by two, but avoid this with more than 3. We're working on this feature in the roadmap.


## How to use

There are 3 ways to use, each one comes with default examples to understand:

- Page 'Analyze with Summary Information': most simple use case, you have the summary data for the whole test and want results.
- Page 'Analyze with Per Impression CSV': you have a CSV with results per impression and want results.
- Page 'Analyze with Per Impression CSV': you have a CSV with summary information per day/week/etc and want results.

## References
* [What is A/B Testing](https://en.wikipedia.org/wiki/A/B_testing)
* [It's time to rethink A/B Testing](https://www.gamedeveloper.com/business/it-s-time-to-re-think-a-b-testing)
* [VWO Website](https://vwo.com/). VWO is a reference on this subject. The bayesian calculations here were implemented based on [this VWO white paper](https://cdn2.hubspot.net/hubfs/310840/VWO_SmartStats_technical_whitepaper.pdf).
* [Agile A/B testing with Bayesian Statistics and Python](https://web.archive.org/web/20150419163005/http://www.bayesianwitch.com/blog/2014/bayesian_ab_test.html)
* [Understanding Bayesian A/B testing (using baseball statistics)](http://varianceexplained.org/r/bayesian_ab_baseball/)
* [It’s time to re-think A/B testing](https://mobiledevmemo.com/its-time-to-abandon-a-b-testing/)
* [Conjugate Priors](https://en.wikipedia.org/wiki/Conjugate_prior)
* [Bayesian A/B Testing Course by Lazy Programmer at Udemy](https://www.udemy.com/course/bayesian-machine-learning-in-python-ab-testing)
* [Binomial Distributions](https://www.youtube.com/watch?v=8idr1WZ1A7Q)
* [Bayes theorem](https://www.youtube.com/watch?v=HZGCoVF3YvM&t=9s)
* [The quick proof of Bayes Theorem](https://www.youtube.com/watch?v=U_85TaXbeIo)

See more more at my [github](https://github.com/lgabs/janus).

""")
