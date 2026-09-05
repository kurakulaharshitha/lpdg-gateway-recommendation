# LPDG Gateway Recommendation Service

A small software service that ranks gateways for weekly field visits using the supplied 3-sigma anomaly baseline.

The service uses only telemetry available before each Monday, ranks gateways based on recent abnormal behaviour, and returns the 15 highest-priority gateways with an operations-friendly explanation.

## What the service does

For each scored Monday:

1. Reads the previous 28 days of gateway telemetry.
2. Calculates each gateway's own historical mean and standard deviation.
3. Checks the most recent 7 days for 3-sigma anomalies.
4. Scores and ranks gateways by anomaly breaches.
5. Returns the top 15 gateways for field visits.
6. Generates `predictions.csv` for all 8 challenge weeks.

## Project Structure

```text
.
├── data/                     # Challenge data (not committed)
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── data_loader.py
│   ├── ranking.py
│   ├── service.py
│   └── api.py
├── tests/
│   ├── test_ranking.py
│   ├── test_service.py
│   ├── test_api.py
│   └── test_end_to_end.py
├── baseline_3sigma.py
├── validate_submission.py
├── predictions.csv
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md