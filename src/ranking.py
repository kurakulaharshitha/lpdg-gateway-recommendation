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

    Gateways that have historical telemetry but incomplete
    recent telemetry remain visible in the ranking, with
    their recent coverage reported explicitly.
    """

    # Prediction cutoff.
    # No telemetry on or after this Monday is allowed.
    end = pd.Timestamp(
        monday,
        tz="UTC",
    )

    # Beginning of the 28-day historical window.
    baseline_start = (
        end
        - dt.timedelta(
            days=BASELINE_DAYS
        )
    )

    # Use only the 28 days strictly before the Monday.
    window = frame[
        (frame["ts"] >= baseline_start)
        & (frame["ts"] < end)
    ].copy()

    if window.empty:
        raise ValueError(
            f"No telemetry data available for the "
            f"{BASELINE_DAYS}-day window before {monday}."
        )

    # Keep every gateway that appeared anywhere in
    # the 28-day window.
    #
    # This prevents a gateway that goes completely silent
    # during the recent 7 days from silently disappearing.
    all_gateways = pd.Index(
        sorted(
            window["gateway_id"].unique()
        ),
        name="gateway_id",
    )

    # Calculate each gateway's own historical
    # mean and standard deviation.
    stats = (
        window
        .groupby("gateway_id")[METRICS]
        .agg(["mean", "std"])
    )

    # Beginning of the recent 7-day period.
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

    # Expected hourly telemetry coverage over 7 days.
    expected_recent_hours = (
        RECENT_DAYS * 24
    )

    # One row can breach more than one metric,
    # so this stores the total number of breached
    # metrics for each telemetry row.
    flags = pd.Series(
        0,
        index=recent.index,
        dtype=int,
    )

    # Used for a simple human-readable explanation.
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

        # A value is anomalous when it is more than
        # 3 standard deviations above that gateway's
        # own historical mean.
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

        # Store the first metric that breached
        # for each telemetry row.
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

    # Aggregate recent anomaly information
    # for gateways that have recent telemetry.
    grouped = (
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
                        for value in values
                        if value
                    ),
                    "",
                ),
            ),
        )
    )

    # Count unique reporting hours rather than raw rows.
    # This also makes duplicate rows less likely to
    # inflate the telemetry-coverage measure.
    recent_hours = (
        recent
        .groupby("gateway_id")["ts"]
        .nunique()
    )

    # Reintroduce gateways that existed in the
    # historical window but had no recent rows.
    ranked = grouped.reindex(
        all_gateways
    )

    # A silent gateway is not automatically labelled
    # faulty. Its anomaly score stays 0, while its
    # missing coverage is surfaced separately.
    ranked["score"] = (
        ranked["score"]
        .fillna(0)
        .astype(int)
    )

    ranked[
        "first_breach_metric"
    ] = (
        ranked[
            "first_breach_metric"
        ]
        .fillna("")
    )

    ranked["recent_hours"] = (
        recent_hours
        .reindex(
            all_gateways,
            fill_value=0,
        )
        .astype(int)
    )

    ranked["coverage_ratio"] = (
        ranked["recent_hours"]
        / expected_recent_hours
    ).clip(
        upper=1.0
    )

    ranked[
        "incomplete_recent_telemetry"
    ] = (
        ranked["recent_hours"]
        < expected_recent_hours
    )

    # Highest anomaly score first.
    # gateway_id is an explicit deterministic
    # tie-breaker.
    ranked = (
        ranked
        .reset_index()
        .sort_values(
            [
                "score",
                "gateway_id",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    return ranked