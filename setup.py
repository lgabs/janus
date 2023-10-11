from setuptools import find_packages, setup

setup(
    name="janus",
    packages=find_packages(include=["janus", "janus.stats", "janus.utils"]),
    version="0.2.0",
    description="Janus, an A/B Test Framework",
    author="Luan Fernandes",
    license="",
    install_requires=[
        "pandas==1.4.4",
        "numpy==1.25.1",
        "scipy==1.11.1",
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest==4.4.1"],
    test_suite="tests",
)
