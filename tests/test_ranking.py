import datetime as dt

import pandas as pd

from src.ranking import rank_gateways_for_week


def make_test_data():
    monday = pd.Timestamp(
        "2026-02-02",
        tz="UTC",
    )

    timestamps = pd.date_range(
        start=monday - pd.Timedelta(days=28),
        end=monday - pd.Timedelta(hours=1),
        freq="h",
    )

    rows = []

    for i, timestamp in enumerate(timestamps):

        # Gateway A - mostly normal, but develops
        # several strong anomalies in the last 7 days.
        offline_a = i % 2
        disconnect_a = i % 3
        reboot_a = i % 5

        if timestamp >= monday - pd.Timedelta(days=7):
            if i % 24 == 0:
                offline_a = 50
                disconnect_a = 20
                reboot_a = 10

        rows.append(
            {
                "gateway_id": "GATEWAY_A",
                "offline_duration_sec": offline_a,
                "disconnection_cnt": disconnect_a,
                "reboot_cnt": reboot_a,
                "ts": timestamp,
            }
        )

        # Gateway B stays fairly normal.
        rows.append(
            {
                "gateway_id": "GATEWAY_B",
                "offline_duration_sec": i % 2,
                "disconnection_cnt": i % 3,
                "reboot_cnt": i % 5,
                "ts": timestamp,
            }
        )

    return pd.DataFrame(rows)


def test_gateway_with_more_anomalies_ranks_first():
    frame = make_test_data()

    result = rank_gateways_for_week(
        frame,
        dt.date(2026, 2, 2),
    )

    assert result.iloc[0]["gateway_id"] == "GATEWAY_A"
    assert result.iloc[0]["score"] > result.iloc[1]["score"]


def test_future_data_is_not_used():
    frame = make_test_data()

    original_result = rank_gateways_for_week(
        frame,
        dt.date(2026, 2, 2),
    )

    future_row = pd.DataFrame(
        [
            {
                "gateway_id": "GATEWAY_B",
                "offline_duration_sec": 999999,
                "disconnection_cnt": 999999,
                "reboot_cnt": 999999,
                "ts": pd.Timestamp(
                    "2026-02-02 01:00:00",
                    tz="UTC",
                ),
            }
        ]
    )

    frame_with_future = pd.concat(
        [frame, future_row],
        ignore_index=True,
    )

    result_with_future = rank_gateways_for_week(
        frame_with_future,
        dt.date(2026, 2, 2),
    )

    pd.testing.assert_frame_equal(
        original_result,
        result_with_future,
    )


def test_equal_scores_use_gateway_id_as_tiebreak():
    monday = pd.Timestamp(
        "2026-02-02",
        tz="UTC",
    )

    timestamps = pd.date_range(
        start=monday - pd.Timedelta(days=28),
        end=monday - pd.Timedelta(hours=1),
        freq="h",
    )

    rows = []

    # Deliberately insert B before A.
    # Both gateways have exactly the same telemetry,
    # so both must receive the same score.
    for i, timestamp in enumerate(timestamps):
        for gateway_id in [
            "GATEWAY_B",
            "GATEWAY_A",
        ]:
            rows.append(
                {
                    "gateway_id": gateway_id,
                    "offline_duration_sec": i % 2,
                    "disconnection_cnt": i % 3,
                    "reboot_cnt": i % 5,
                    "ts": timestamp,
                }
            )

    frame = pd.DataFrame(rows)

    result = rank_gateways_for_week(
        frame,
        dt.date(2026, 2, 2),
    )

    # Their scores must tie.
    assert result["score"].nunique() == 1

    # Even though B was inserted first,
    # gateway_id must deterministically break the tie.
    assert result["gateway_id"].tolist() == [
        "GATEWAY_A",
        "GATEWAY_B",
    ]


def test_gateway_with_no_recent_rows_does_not_disappear():
    monday = pd.Timestamp(
        "2026-02-02",
        tz="UTC",
    )

    historical_timestamps = pd.date_range(
        start=monday - pd.Timedelta(days=28),
        end=monday - pd.Timedelta(days=8),
        freq="h",
    )

    recent_timestamps = pd.date_range(
        start=monday - pd.Timedelta(days=7),
        end=monday - pd.Timedelta(hours=1),
        freq="h",
    )

    rows = []

    # This gateway reported historically,
    # but is completely silent during the recent 7 days.
    for timestamp in historical_timestamps:
        rows.append(
            {
                "gateway_id": "SILENT_GATEWAY",
                "offline_duration_sec": 0,
                "disconnection_cnt": 0,
                "reboot_cnt": 0,
                "ts": timestamp,
            }
        )

    # This gateway continues reporting normally.
    for timestamp in (
        list(historical_timestamps)
        + list(recent_timestamps)
    ):
        rows.append(
            {
                "gateway_id": "ACTIVE_GATEWAY",
                "offline_duration_sec": 0,
                "disconnection_cnt": 0,
                "reboot_cnt": 0,
                "ts": timestamp,
            }
        )

    frame = pd.DataFrame(rows)

    result = rank_gateways_for_week(
        frame,
        dt.date(2026, 2, 2),
    )

    # The silent gateway must still exist in the result.
    assert "SILENT_GATEWAY" in result["gateway_id"].tolist()

    silent = result[
        result["gateway_id"]
        == "SILENT_GATEWAY"
    ].iloc[0]

    # Silence is not automatically classified as a fault.
    assert silent["score"] == 0

    # But missing recent telemetry is explicitly visible.
    assert silent["recent_hours"] == 0
    assert silent["coverage_ratio"] == 0.0

    assert bool(
        silent["incomplete_recent_telemetry"]
    ) is True