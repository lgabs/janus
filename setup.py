from setuptools import find_packages, setup

setup(
    name="janus",
    packages=find_packages(include=["janus", "janus.stats", "janus.utils"]),
    version="0.1.1",
    description="Janus, an A/B Test Framework",
    author="Luan Fernandes",
    license="",
    install_requires=[
        "pandas==0.25.3",
        "numpy==1.19.1",
        "scipy==1.5.2",
        "pyspark==3.0.0",
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest==4.4.1"],
    test_suite="tests",
)
