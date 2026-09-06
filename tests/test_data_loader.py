from pathlib import Path

import pytest

from src.data_loader import load_telemetry


def test_missing_telemetry_folder_fails_clearly(tmp_path: Path):
    missing_data_dir = tmp_path / "missing-data"

    with pytest.raises(
        FileNotFoundError,
        match="Telemetry folder not found",
    ):
        load_telemetry(
            data_dir=missing_data_dir
        )