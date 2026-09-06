from .config import OUTPUT_PATH
from .data_loader import load_telemetry
from .service import write_predictions


def main() -> int:
    """
    Generate predictions.csv using the latest available telemetry.
    """

    frame = load_telemetry()

    predictions = write_predictions(
        output_path=OUTPUT_PATH,
        frame=frame,
    )

    print(
        f"Wrote {OUTPUT_PATH} — "
        f"{len(predictions)} rows over "
        f"{predictions['week_start'].nunique()} weeks"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())