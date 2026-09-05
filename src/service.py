import datetime as dt
from pathlib import Path

import pandas as pd

from .config import (
    OUTPUT_PATH,
    SCORED_WEEKS,
    VISITS_PER_WEEK,
)
from .data_loader import (
    load_telemetry,
)
from .ranking import (
    rank_gateways_for_week,
)


FRIENDLY_METRIC_NAMES = {
    "offline_duration_sec": "offline time",
    "disconnection_cnt": "connection dropouts",
    "reboot_cnt": "reboots",
}


def build_reason(
    score: float,
    metric: str,
) -> str:
    """
    Convert technical anomaly information into
    a short operations-friendly explanation.
    """

    friendly_metric = (
        FRIENDLY_METRIC_NAMES.get(
            metric,
            "gateway health signals",
        )
    )

    return (
        f"{int(score)} anomaly breach(es) were detected "
        f"in the last 7 days compared with this gateway's "
        f"previous 28-day behavior; the first abnormal "
        f"signal was {friendly_metric}."
    )


def get_weekly_recommendations(
    monday: dt.date,
    frame: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Return the top gateways recommended for a
    field visit for one Monday.
    """

    if frame is None:
        frame = load_telemetry()

    ranked = rank_gateways_for_week(
        frame,
        monday,
    )

    if len(ranked) < VISITS_PER_WEEK:
        raise ValueError(
            f"Only {len(ranked)} gateways could be ranked "
            f"for {monday}; {VISITS_PER_WEEK} are required."
        )

    top = (
        ranked
        .head(VISITS_PER_WEEK)
        .copy()
    )

    top["rank"] = range(
        1,
        len(top) + 1,
    )

    top["week_start"] = (
        monday.isoformat()
    )

    top["reason"] = top.apply(
        lambda row: build_reason(
            row["score"],
            row[
                "first_breach_metric"
            ],
        ),
        axis=1,
    )

    return top[
        [
            "week_start",
            "rank",
            "gateway_id",
            "score",
            "reason",
        ]
    ]


def get_gateway_explanation(
    monday: dt.date,
    gateway_id: str,
    frame: pd.DataFrame | None = None,
) -> dict:
    """
    Explain where a gateway appears in the ranking
    for a particular week.
    """

    if frame is None:
        frame = load_telemetry()

    gateway_exists = (
        frame["gateway_id"]
        .eq(gateway_id)
        .any()
    )

    if not gateway_exists:
        raise KeyError(
            f"Gateway '{gateway_id}' does not exist."
        )

    ranked = rank_gateways_for_week(
        frame,
        monday,
    )

    match = ranked[
        ranked["gateway_id"]
        == gateway_id
    ]

    if match.empty:
        raise ValueError(
            f"Gateway '{gateway_id}' has no ranking data "
            f"for week {monday}."
        )

    index = int(
        match.index[0]
    )

    position = index + 1

    row = match.iloc[0]

    metric = str(
        row[
            "first_breach_metric"
        ]
    )

    return {
        "week_start": monday.isoformat(),
        "gateway_id": gateway_id,
        "rank": position,
        "selected_for_visit": (
            position
            <= VISITS_PER_WEEK
        ),
        "score": float(
            row["score"]
        ),
        "first_abnormal_signal": (
            FRIENDLY_METRIC_NAMES.get(
                metric,
                "gateway health signals",
            )
        ),
        "reason": build_reason(
            row["score"],
            metric,
        ),
    }


def build_all_predictions(
    frame: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Generate the required recommendations for
    all 8 scored challenge weeks.
    """

    if frame is None:
        frame = load_telemetry()

    weekly_results = []

    for monday in SCORED_WEEKS:

        weekly = (
            get_weekly_recommendations(
                monday=monday,
                frame=frame,
            )
        )

        weekly_results.append(
            weekly
        )

    return pd.concat(
        weekly_results,
        ignore_index=True,
    )


def write_predictions(
    output_path: Path = OUTPUT_PATH,
    frame: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Regenerate predictions.csv from the current data.
    """

    predictions = (
        build_all_predictions(
            frame=frame,
        )
    )

    predictions.to_csv(
        output_path,
        index=False,
    )

    return predictions