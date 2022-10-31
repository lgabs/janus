import pandas as pd
from janus.utils.make_dataframe_multivariate import (
    create_per_user_dataframe_multivariate,
)


df = pd.read_csv("dataset_summary_copy.csv")

print(df)

df2 = create_per_user_dataframe_multivariate(df)

print(df2)
