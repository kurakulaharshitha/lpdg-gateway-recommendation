import datetime as dt

import numpy as np
import pandas as pd

from .config import (
    BASELINE_DAYS,
    METRICS,
    RECENT_DAYS,
    SIGMA,
)


def rank_gateways_for_week(
    frame: pd.DataFrame,
    monday: dt.date,
) -> pd.DataFrame:
    """
    Rank gateways for one Monday using the supplied
    3-sigma baseline logic.

    Only telemetry strictly before the Monday is used.
    """

    end = pd.Timestamp(
        monday,
        tz="UTC",
    )

    baseline_start = (
        end
        - dt.timedelta(
            days=BASELINE_DAYS
        )
    )

    window = frame[
        (frame["ts"] >= baseline_start)
        & (frame["ts"] < end)
    ].copy()

    if window.empty:
        raise ValueError(
            f"No telemetry data available for the "
            f"{BASELINE_DAYS}-day window before {monday}."
        )

    stats = (
        window
        .groupby("gateway_id")[METRICS]
        .agg(["mean", "std"])
    )

    recent_start = (
        end
        - dt.timedelta(
            days=RECENT_DAYS
        )
    )

    recent = window[
        window["ts"] >= recent_start
    ].copy()

    if recent.empty:
        raise ValueError(
            f"No telemetry available in the "
            f"{RECENT_DAYS} days before {monday}."
        )

    flags = pd.Series(
        0,
        index=recent.index,
        dtype=int,
    )

    first_breach_metric = pd.Series(
        "",
        index=recent.index,
        dtype=object,
    )

    for metric in METRICS:

        gateway_mean = (
            recent["gateway_id"]
            .map(
                stats[
                    (metric, "mean")
                ]
            )
        )

        gateway_std = (
            recent["gateway_id"]
            .map(
                stats[
                    (metric, "std")
                ]
            )
            .replace(
                0,
                np.nan,
            )
        )

        exceeded = (
            recent[metric]
            - gateway_mean
        ) > (
            SIGMA
            * gateway_std
        )

        exceeded = (
            exceeded
            .fillna(False)
        )

        flags = (
            flags
            + exceeded.astype(int)
        )

        first_breach_metric = (
            first_breach_metric.where(
                ~exceeded
                | (
                    first_breach_metric
                    != ""
                ),
                metric,
            )
        )

    recent["flagged"] = flags

    recent[
        "first_breach_metric"
    ] = first_breach_metric

    ranked = (
        recent
        .groupby("gateway_id")
        .agg(
            score=(
                "flagged",
                "sum",
            ),
            first_breach_metric=(
                "first_breach_metric",
                lambda values: next(
                    (
                        value
                        for value
                        in values
                        if value
                    ),
                    "",
                ),
            ),
        )
        .sort_values(
    ["score", "gateway_id"],
    ascending=[False, True],
)
        .reset_index()
    )

    return ranked