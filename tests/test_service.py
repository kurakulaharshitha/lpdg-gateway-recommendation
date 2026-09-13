import datetime as dt

from src.data_loader import load_telemetry
from src.service import get_weekly_recommendations


def test_weekly_recommendations_have_15_gateways():
    frame = load_telemetry()

    result = get_weekly_recommendations(
        dt.date(2026, 2, 2),
        frame=frame,
    )

    assert len(result) == 15


def test_weekly_recommendation_ranks_are_1_to_15():
    frame = load_telemetry()

    result = get_weekly_recommendations(
        dt.date(2026, 2, 2),
        frame=frame,
    )

    assert result["rank"].tolist() == list(range(1, 16))


def test_weekly_recommendations_have_expected_columns():
    frame = load_telemetry()

    result = get_weekly_recommendations(
        dt.date(2026, 2, 2),
        frame=frame,
    )

    assert result.columns.tolist() == [
        "week_start",
        "rank",
        "gateway_id",
        "score",
        "reason",
    ]


def test_reasons_are_not_empty():
    frame = load_telemetry()

    result = get_weekly_recommendations(
        dt.date(2026, 2, 2),
        frame=frame,
    )

    assert result["reason"].notna().all()
    assert result["reason"].str.strip().ne("").all()


def test_reasons_do_not_exceed_300_characters():
    frame = load_telemetry()

    result = get_weekly_recommendations(
        dt.date(2026, 2, 2),
        frame=frame,
    )

    assert result["reason"].str.len().le(300).all()