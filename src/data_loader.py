from pathlib import Path

import pandas as pd

from .config import DATA_DIR, METRICS


def load_telemetry(
    data_dir: Path = DATA_DIR,
) -> pd.DataFrame:
    """
    Load only the telemetry columns required by the ranking algorithm.
    """

    telemetry_path = data_dir / "telemetry"

    if not telemetry_path.exists():
        raise FileNotFoundError(
            f"Telemetry folder not found: {telemetry_path}"
        )

    columns = [
        "gateway_id",
        "ts_utc",
        *METRICS,
    ]

    try:
        frame = pd.read_parquet(
            telemetry_path,
            columns=columns,
        )
    except Exception as exc:
        raise ValueError(
            f"Unable to read telemetry data: {exc}"
        ) from exc

    if frame.empty:
        raise ValueError(
            "Telemetry data is empty."
        )

    required_columns = {
        "gateway_id",
        "ts_utc",
        *METRICS,
    }

    missing_columns = required_columns - set(frame.columns)

    if missing_columns:
        raise ValueError(
            "Telemetry is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    frame["ts"] = pd.to_datetime(
        frame["ts_utc"],
        utc=True,
        errors="coerce",
    )

    if frame["ts"].isna().any():
        invalid_count = int(
            frame["ts"].isna().sum()
        )

        raise ValueError(
            f"Telemetry contains {invalid_count} invalid timestamp(s)."
        )

    if frame["gateway_id"].isna().any():
        raise ValueError(
            "Telemetry contains missing gateway IDs."
        )

    return frame.drop(
        columns=["ts_utc"]
    )