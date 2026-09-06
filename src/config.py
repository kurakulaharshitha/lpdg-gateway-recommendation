import datetime as dt
import os
from pathlib import Path


DATA_DIR = Path(
    os.getenv("DATA_DIR", "data")
)

OUTPUT_PATH = Path(
    os.getenv("OUTPUT_PATH", "predictions.csv")
)

METRICS = [
    "offline_duration_sec",
    "disconnection_cnt",
    "reboot_cnt",
]

VISITS_PER_WEEK = 15
BASELINE_DAYS = 28
RECENT_DAYS = 7
SIGMA = 3.0

SCORED_WEEKS = [
    dt.date(2026, 2, 2) + dt.timedelta(days=7 * i)
    for i in range(8)
]