import subprocess
import sys
from pathlib import Path

import pandas as pd

from src.data_loader import load_telemetry
from src.service import write_predictions


def test_end_to_end_prediction_generation(tmp_path):
    """
    Run the real prediction pipeline from telemetry input
    through CSV creation, then check the output with the
    challenge's official validation script.
    """

    output_file = tmp_path / "predictions.csv"

    frame = load_telemetry()

    predictions = write_predictions(
        output_path=output_file,
        frame=frame,
    )

    # The challenge requires 8 weeks x 15 gateways.
    assert len(predictions) == 120

    assert predictions["week_start"].nunique() == 8

    # Every week must contain exactly 15 recommendations.
    counts = (
        predictions
        .groupby("week_start")
        .size()
    )

    assert (counts == 15).all()

    # The generated CSV must actually exist.
    assert output_file.exists()

    # Read it back from disk to make sure the written file is valid.
    written = pd.read_csv(output_file)

    assert len(written) == 120

    assert written.columns.tolist() == [
        "week_start",
        "rank",
        "gateway_id",
        "score",
        "reason",
    ]

    # Finally run the challenge's own validator.
    project_root = Path(__file__).resolve().parents[1]

    validator = project_root / "validate_submission.py"

    validation = subprocess.run(
        [
            sys.executable,
            str(validator),
            str(output_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert validation.returncode == 0, (
        validation.stdout
        + validation.stderr
    )

    assert "OK" in validation.stdout