import datetime as dt
from functools import lru_cache

import pandas as pd
from fastapi import (
    FastAPI,
    HTTPException,
)

from .data_loader import (
    load_telemetry,
)
from .service import (
    get_gateway_explanation,
    get_weekly_recommendations,
    write_predictions,
)


app = FastAPI(
    title=(
        "LPDG Gateway "
        "Recommendation API"
    ),
    description=(
        "Ranks gateways for field visits "
        "using recent telemetry anomalies."
    ),
    version="1.0.0",
)


@lru_cache(maxsize=1)
def get_telemetry() -> pd.DataFrame:
    """
    Load telemetry once and reuse it between
    normal API requests.
    """

    return load_telemetry()


@app.get("/")
def root():
    """
    Basic information about the service.
    """

    return {
        "service": (
            "LPDG Gateway "
            "Recommendation API"
        ),
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
def health():
    """
    Check whether the service can access
    and read the telemetry data.
    """

    try:
        frame = get_telemetry()

        return {
            "status": "healthy",
            "telemetry_rows": len(frame),
            "gateway_count": int(
                frame[
                    "gateway_id"
                ].nunique()
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Service is unhealthy: "
                f"{exc}"
            ),
        ) from exc


@app.get(
    "/recommendations/{week_start}"
)
def recommendations(
    week_start: dt.date,
):
    """
    Return the 15 recommended gateways
    for a particular Monday.
    """

    if week_start.weekday() != 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "week_start must "
                "be a Monday."
            ),
        )

    try:
        frame = get_telemetry()

        result = (
            get_weekly_recommendations(
                monday=week_start,
                frame=frame,
            )
        )

        return {
            "week_start": (
                week_start.isoformat()
            ),
            "count": len(result),
            "recommendations": (
                result.to_dict(
                    orient="records"
                )
            ),
        }

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@app.get(
    "/gateways/"
    "{gateway_id}/explanation"
)
def gateway_explanation(
    gateway_id: str,
    week_start: dt.date,
):
    """
    Explain a gateway's score and ranking
    for a particular week.
    """

    if week_start.weekday() != 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "week_start must "
                "be a Monday."
            ),
        )

    try:
        frame = get_telemetry()

        return get_gateway_explanation(
            monday=week_start,
            gateway_id=gateway_id,
            frame=frame,
        )

    except KeyError as exc:
        message = (
            exc.args[0]
            if exc.args
            else str(exc)
        )

        raise HTTPException(
            status_code=404,
            detail=message,
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@app.post("/run")
def rerun_predictions():
    """
    Reload the latest data and regenerate
    predictions.csv for all challenge weeks.
    """

    try:
        # Important:
        # clear the in-memory copy so /run
        # really reads fresh input data.
        get_telemetry.cache_clear()

        frame = get_telemetry()

        predictions = (
            write_predictions(
                frame=frame,
            )
        )

        return {
            "status": "completed",
            "output_file": (
                "predictions.csv"
            ),
            "rows_written": len(
                predictions
            ),
            "weeks": int(
                predictions[
                    "week_start"
                ].nunique()
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Prediction run failed: "
                f"{exc}"
            ),
        ) from exc