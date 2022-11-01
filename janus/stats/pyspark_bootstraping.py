# Databricks notebook source

# código de exemplo
# https://medium.com/udemy-engineering/bootstrapping-with-spark-f7ac338702d6

# Porque o spark não pode ser usado para paralelizar completamente o processo
# https://medium.com/udemy-engineering/pyspark-under-the-hood-randomsplit-and-sample-inconsistencies-examined-7c6ec62644bc

# Alternativa para acelerar: construir a função de média
# do sample em scala e chamar dentro do Python
# https://aseigneurin.github.io/2016/09/01/spark-calling-scala-code-from-pyspark.html
# https://community.cloudera.com/t5/Support-Questions/Is-it-possible-to-call-a-scala-function-in-python-pyspark/td-p/174835

from typing import List, Union
import random as rd
from pyspark.sql import SparkSession, DataFrame as SparkDataFrame


def get_bootstraped_mean(data: List[Union[float, int]]) -> float:
    n_samples = len(data)
    samples = [data[rd.randint(0, n_samples - 1)] for _ in range(0, n_samples)]
    return sum(samples) / n_samples


def get_parallel_bootstrap(
    function,
    data: List[Union[float, int]],
    num_samples: int,
    spark_session: SparkSession,
) -> SparkDataFrame:
    rdd = spark_session.sparkContext.parallelize(list(range(1, num_samples + 1)))
    df = (
        rdd.map(lambda x: (x, function(data)))
        .toDF()
        .withColumnRenamed("_1", "sample")
        .withColumnRenamed("_2", "sample_metric")
    )
    return df
