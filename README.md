# Janus

![License2](https://img.shields.io/github/license/lgabs/janus)
![Python Version](https://img.shields.io/badge/python-3.7%20%7C%203.8-brightgreen.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **Warning**
> We're making a major breaking change in the project to use the [bayesian-testing](https://github.com/Matt52/bayesian-testing) library for better experiment management, and a full stack application will be developed to build a website for Janus.
> Please, consider using the distributed [package in pypi](https://pypi.org/project/janus-web-ab-testing/), which comes from the `evolve-janus-backend` branch.


Janus is an A/B Test Engine to be used in a variety use cases, especially to measure conversion, ticket and ARPU difference between variants, i.e, typical metrics for tests in marketplaces. The engine name is an analogy to _Janus_, the god of changes and transitions.

This library came as an ideia of separate the statistical calculations in A/B Tests from other code that is typically used to manage tests and execute queries over the company's database, and hence usually carry proprietary code and even business logic, which should not be open sourced. There was the bud to build this library and get it open sourced.

Checkout the [streamlit app](https://lgabs-janus-homepage-31diny.streamlit.app/) from this repo.

## Installation

Open a terminal, clone this repository into your machine and stay into the project directory.

Using a virtual environment is a good practice, but it is optional. If you enjoy it, go ahead and create a virtual environment by typing:
```
python3 -m venv venv -r requirements.txt
```
Once it is created, you must now activate the environment by using:
```
source venv/bin/activate
```
Now, you can install our lib (if you are not using virtual env, go straight to this command):
```
make install
```

And that's it! Now, inside our environment, we can import the `janus` lib inside our scripts with plain `import janus` etc. Try to test using the same code on `experiment_example.ipynb` notebook here or in a plain terminal. 

## Using as an Application

You can use _janus_ as a streamlit product in two ways:

### 1. Using Docker (Recommended)
Build and run the application locally using Docker:
```bash
# Build the Docker image
docker build -t janus .

# Run the container
docker run -p 8501:8501 janus
```
Or use `make run`. Then open your browser and navigate to `http://localhost:8501`


## References
* [What is A/B Testing](https://en.wikipedia.org/wiki/A/B_testing)
* The bayesian calculations were implemented based on [this VWO white paper](https://cdn2.hubspot.net/hubfs/310840/VWO_SmartStats_technical_whitepaper.pdf)
* [VWO Website](https://vwo.com/)
* [Agile A/B testing with Bayesian Statistics and Python](https://web.archive.org/web/20150419163005/http://www.bayesianwitch.com/blog/2014/bayesian_ab_test.html)
* [Understanding Bayesian A/B testing (using baseball statistics)](http://varianceexplained.org/r/bayesian_ab_baseball/)
* [It's time to re-think A/B testing](https://mobiledevmemo.com/its-time-to-abandon-a-b-testing/)
* [Conjugate Priors](https://en.wikipedia.org/wiki/Conjugate_prior)
* [Curso de Teste A/B Bayesiano do Lazy Programmer](https://www.udemy.com/course/bayesian-machine-learning-in-python-ab-testing)
* [Binomial Distributions](https://www.youtube.com/watch?v=8idr1WZ1A7Q)
* [Bayes theorem](https://www.youtube.com/watch?v=HZGCoVF3YvM&t=9s)
* [The quick proof of Bayes Theorem](https://www.youtube.com/watch?v=U_85TaXbeIo)
