import streamlit as st

import logging
from utils import print_warning

st.set_page_config(page_title="Why Bayesian?", page_icon="📊")

logging.basicConfig(level=logging.INFO)

print_warning()

st.markdown(
    """
# 📊 Why Bayesian?

This engine is more powerful than common online websites becasue it measures statistics for 3 very important variables at once: 
- **conversion rate** (e.g., percentage of visits that turn into sales)
- **monetary value for conversions** (e.g., revenue per transaction) 
- **average value per impression** (e.g., Average Revenue per User)

Sometimes, conversion rate is not the best metric for your test: sometimes the most important is if you're bringing more money to the table. That's why ARPU helps you a lot. Revenue also helps you to undestand how your ticket sale is affected between variants.

These are not usual even in famous tools like [abtestguide](https://abtestguide.com/bayesian/) or their [frequentist approach](https://abtestguide.com/calc/), because they only measures for conversion rate.\n


See below the main advantages of this method:
"""
)

st.image("stats-differences.png")


st.markdown(
    """
## References
* [What is A/B Testing](https://en.wikipedia.org/wiki/A/B_testing)
* [Its time to rethink A/B Testing](https://www.gamedeveloper.com/business/it-s-time-to-re-think-a-b-testing)
* [VWO Website](https://vwo.com/). VWO is a reference on this subject. The bayesian calculations here were implemented based on [this VWO white paper](https://cdn2.hubspot.net/hubfs/310840/VWO_SmartStats_technical_whitepaper.pdf).
* [Agile A/B testing with Bayesian Statistics and Python](https://web.archive.org/web/20150419163005/http://www.bayesianwitch.com/blog/2014/bayesian_ab_test.html)
* [Understanding Bayesian A/B testing (using baseball statistics)](http://varianceexplained.org/r/bayesian_ab_baseball/)
* [It’s time to abandon A/B testing](https://mobiledevmemo.com/its-time-to-abandon-a-b-testing/)
* [Conjugate Priors](https://en.wikipedia.org/wiki/Conjugate_prior)
* [Bayesian A/B Testing Course by Lazy Programmer at Udemy](https://www.udemy.com/course/bayesian-machine-learning-in-python-ab-testing)
* [Binomial Distributions](https://www.youtube.com/watch?v=8idr1WZ1A7Q)
* [Bayes theorem](https://www.youtube.com/watch?v=HZGCoVF3YvM&t=9s)
* [The quick proof of Bayes Theorem](https://www.youtube.com/watch?v=U_85TaXbeIo)

See more more at my [github](https://github.com/lgabs/janus).

"""
)
