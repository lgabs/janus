![janus](logo.png)
# Janus

![License2](https://img.shields.io/github/license/lgabs/janus)
![Python Version](https://img.shields.io/badge/python-3.7%20%7C%203.8-brightgreen.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Janus is a simple and easy A/B Test Calculator that allows you to run A/B tests and get reports in a few lines of code. 

It's developed mainly for website experiments. While many calculators only account for conversion analysis and consider only two variants, Janus allows multivariant tests and measure _Conversion_, _Averge Ticket_ and _Average Revenue Per User (ARPU)_ over variants, i.e, typical metrics for tests in marketplaces. 

The engine name is an analogy to _Janus_, the god of changes and transitions.


## Installation

Janus is distributed in [pypi](https://pypi.org/project/janus-web-ab-testing/). You can install it by using:
```
pip install janus-web-ab-testing
```

You can now run a quick example of a A/B test:
```
from janus.variant import Variant
from janus.experiment import WebsiteExperiment

variant_A = Variant(
    name="A",
    impressions=1000, 
    conversions=100, 
    revenue=10000
)
variant_B = Variant(
    name="B",
    impressions=1000, 
    conversions=120, 
    revenue=9000
)
variants = [variant_A, variant_B]

experiment = WebsiteExperiment(variants, baseline_variant="A")
experiment.run()
experiment.print_reports()
```

See more in the [quickstart notebook](examples/Janus%20Quickstart.ipynb).

## The Janus Website

My plan is to build a website to showcase the Janus library and to provide a simple interface to run A/B tests. However, only the library is almost ready, and the next steps would be:
- build a backend with FastAPI using the library
- build a frontend (JavaScript maybe)
- deploy the website


## References
* [What is A/B Testing](https://en.wikipedia.org/wiki/A/B_testing)
* [VWO paper about bayesian A/B testing](https://vwo.com/downloads/VWO_SmartStats_technical_whitepaper.pdf)
* [Agile A/B testing with Bayesian Statistics and Python](https://web.archive.org/web/20150419163005/http://www.bayesianwitch.com/blog/2014/bayesian_ab_test.html)
* [Understanding Bayesian A/B testing (using baseball statistics)](http://varianceexplained.org/r/bayesian_ab_baseball/)
* [It’s time to re-think A/B testing](https://mobiledevmemo.com/its-time-to-abandon-a-b-testing/)
* [Conjugate Priors](https://en.wikipedia.org/wiki/Conjugate_prior)
* [Curso de Teste A/B Bayesiano do Lazy Programmer](https://www.udemy.com/course/bayesian-machine-learning-in-python-ab-testing)
* [Binomial Distributions](https://www.youtube.com/watch?v=8idr1WZ1A7Q)
* [Bayes theorem](https://www.youtube.com/watch?v=HZGCoVF3YvM&t=9s)
* [The quick proof of Bayes Theorem](https://www.youtube.com/watch?v=U_85TaXbeIo)
