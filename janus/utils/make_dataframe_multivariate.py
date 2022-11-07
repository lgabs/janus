from typing import List, Union
import numpy as np
import pandas as pd


def create_per_user_dataframe_multivariate(
    df_summary_daily: pd.DataFrame,
    conversion_value_cols: List[str],
):
    """
    Produces a per-user dataframe using data from summary of an experiment on
    some period basis like daily. The best case is to extract this data from
    your sources, but this approximation will work in the absence of this data
    and with much more insights.

    The arguments are mostly referenced in list of values per variant. It is
    designed to be used in a for-loop for each period summary.

    Args:
    """
    # check columns
    ALLOWED_COLS = [
        "alternative",
        "exposure_period",
        "exposures",
        "conversions",
    ] + conversion_value_cols

    assert set(ALLOWED_COLS).issubset(
        set(df_summary_daily.columns)
    ), f"Use allowed cols plus 'conversion_value_cols': {ALLOWED_COLS}. Your cols are: {list(df_summary_daily.columns)}"

    df = pd.DataFrame(
        columns=[
            "alternative",
            "user_id",
            "exposure_period",
            "converted",
        ]
        + conversion_value_cols
    )

    # fix datetimes
    df_summary_daily["exposure_period"] = pd.to_datetime(
        df_summary_daily["exposure_period"]
    )

    # basic variables
    variants = list(df_summary_daily.alternative.unique())
    periods = list(df_summary_daily.exposure_period.unique())
    all_users = []

    # loop per period
    for period in periods:
        for variant in variants:
            _df = df_summary_daily[
                (df_summary_daily.exposure_period == period)
                & (df_summary_daily.alternative == variant)
            ]
            exposures = _df.exposures.values[0]
            conversions = _df.conversions.values[0]
            not_converted = exposures - conversions

            alternative_converted = np.repeat(variant, conversions)
            alternative_not_converted = np.repeat(variant, not_converted)
            did_user_converted = np.repeat(1, conversions)
            did_users_not_converted = np.repeat(0, not_converted)

            start_id = all_users[-1] + 1 if all_users else 1
            user_id = np.linspace(start_id, start_id + exposures - 1, exposures)
            user_id = [int(i) for i in user_id]
            user_id_converted = user_id[:conversions]
            user_id_not_converted = user_id[conversions:]
            all_users.extend(user_id_converted)
            all_users.extend(user_id_not_converted)

            # simulates that every user converted the same value
            conversion_values_per_user_converted = {}
            conversion_values_per_user_not_converted = {}
            for conversion_col in conversion_value_cols:
                conversion_values_per_user_converted[conversion_col] = np.repeat(
                    _df[conversion_col].values[0] / conversions, conversions
                )
                conversion_values_per_user_not_converted[conversion_col] = np.repeat(
                    0, not_converted
                )

            # Generate dataframes
            data_converted = {
                "alternative": alternative_converted,
                "user_id": user_id_converted,
                "exposure_period": [period] * len(user_id_converted),
                "converted": did_user_converted,
            }
            data_converted.update(conversion_values_per_user_converted)
            # return data_converted
            df_converted = pd.DataFrame(data=data_converted)

            data_not_converted = {
                "alternative": alternative_not_converted,
                "user_id": user_id_not_converted,
                "exposure_period": [period] * len(user_id_not_converted),
                "converted": did_users_not_converted,
            }
            data_not_converted.update(conversion_values_per_user_not_converted)
            df_not_converted = pd.DataFrame(data=data_not_converted)

            # Gather
            df_period = pd.concat([df_converted, df_not_converted], axis=0)
            df = pd.concat([df, df_period], axis=0)

    return df
