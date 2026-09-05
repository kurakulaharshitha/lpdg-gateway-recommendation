# LPDG Gateway Recommendation Service

A production-style API service that ranks gateways for weekly field visits using the supplied 3-sigma anomaly baseline.

The system uses only telemetry available before each Monday, identifies gateways showing unusual recent behaviour, ranks them by anomaly severity, and returns the 15 gateways that should be prioritised for field visits.

This submission focuses on **Software Development** for Part 2 of the LPDG Innovation Hub Selection Challenge.

---

## Quick Start

Make sure the challenge data is available in:

```text
./data
```

Start the complete application with:

```bash
docker compose up --build
```

Then open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

The API will be available at:

```text
http://127.0.0.1:8000
```

To stop the application:

```text
Ctrl + C
```

---

## What the Service Does

For each scored Monday, the service:

1. Reads the previous 28 days of telemetry.
2. Calculates the mean and standard deviation for each gateway's:
   - offline duration
   - disconnection count
   - reboot count
3. Examines the most recent 7 days.
4. Flags values more than 3 standard deviations above that gateway's own baseline.
5. Counts anomaly breaches.
6. Ranks gateways from highest to lowest anomaly score.
7. Returns the top 15 gateways.
8. Provides a human-readable explanation for each recommendation.

Only telemetry strictly before the prediction Monday is used.

This prevents future-data leakage.

---

## Challenge Output

The generated submission file is:

```text
predictions.csv
```

It contains:

```text
week_start
rank
gateway_id
score
reason
```

The service produces exactly:

```text
8 weeks × 15 gateways = 120 rows
```

for:

```text
2026-02-02
2026-02-09
2026-02-16
2026-02-23
2026-03-02
2026-03-09
2026-03-16
2026-03-23
```

The challenge requires exactly this 120-row structure. :contentReference[oaicite:0]{index=0}

---

## API Endpoints

### 1. Service Information

```http
GET /
```

Returns basic information about the running service.

Example response:

```json
{
  "service": "LPDG Gateway Recommendation API",
  "version": "1.0.0",
  "status": "running"
}
```

---

### 2. Health Check

```http
GET /health
```

Checks that the service is running and that telemetry can be loaded successfully.

Example response:

```json
{
  "status": "healthy",
  "telemetry_rows": 1433387,
  "gateway_count": 320
}
```

---

### 3. Weekly Recommendations

```http
GET /recommendations/{week_start}
```

Example:

```text
GET /recommendations/2026-02-02
```

Returns the 15 highest-priority gateways for that Monday.

Example response:

```json
{
  "week_start": "2026-02-02",
  "count": 15,
  "recommendations": [
    {
      "week_start": "2026-02-02",
      "rank": 1,
      "gateway_id": "0A2778A31BE3",
      "score": 43,
      "reason": "43 anomaly breach(es) were detected in the last 7 days compared with this gateway's previous 28-day behavior; the first abnormal signal was connection dropouts."
    }
  ]
}
```

The supplied date must be a Monday.

Invalid dates are returned as a clear HTTP error rather than silently producing a result.

---

### 4. Gateway Explanation

```http
GET /gateways/{gateway_id}/explanation?week_start=YYYY-MM-DD
```

Example:

```text
GET /gateways/0A2778A31BE3/explanation?week_start=2026-02-02
```

Returns information about why a particular gateway appears where it does in the ranking.

Example response:

```json
{
  "week_start": "2026-02-02",
  "gateway_id": "0A2778A31BE3",
  "rank": 1,
  "selected_for_visit": true,
  "score": 43,
  "first_abnormal_signal": "connection dropouts",
  "reason": "43 anomaly breach(es) were detected in the last 7 days compared with this gateway's previous 28-day behavior; the first abnormal signal was connection dropouts."
}
```

An unknown gateway returns HTTP `404`.

---

### 5. Re-run Predictions

```http
POST /run
```

Reloads the latest telemetry and regenerates `predictions.csv`.

Example response:

```json
{
  "status": "completed",
  "output_file": "predictions.csv",
  "rows_written": 120,
  "weeks": 8
}
```

The telemetry cache is cleared before rerunning so newly arrived data is used.

---

## Project Structure

```text
LPDG-Challenge/
│
├── data/                         # Challenge data - not committed
│
├── src/
│   ├── __init__.py
│   ├── config.py                 # Shared configuration
│   ├── data_loader.py            # Telemetry loading and validation
│   ├── ranking.py                # 3-sigma ranking algorithm
│   ├── service.py                # Business logic and explanations
│   └── api.py                    # FastAPI HTTP interface
│
├── tests/
│   ├── test_ranking.py
│   ├── test_service.py
│   ├── test_api.py
│   └── test_end_to_end.py
│
├── baseline_3sigma.py            # Supplied baseline
├── validate_submission.py        # Supplied validator
├── predictions.csv
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
│
├── README.md
├── README.txt
├── DECISIONS.md
├── LIMITATIONS.md
└── AI-USAGE.md
```

---

## Architecture

The application deliberately separates responsibilities.

```text
               HTTP Client
                    |
                    v
                FastAPI
                 api.py
                    |
                    v
               service.py
                    |
                    v
               ranking.py
                    |
                    v
             data_loader.py
                    |
                    v
             data/telemetry
```

### `data_loader.py`

Responsible for:

- locating telemetry
- loading only required columns
- parsing timestamps
- detecting missing or invalid data

### `ranking.py`

Responsible only for:

- selecting the historical window
- calculating gateway-specific statistics
- identifying 3-sigma anomalies
- ranking gateways

### `service.py`

Responsible for:

- selecting the top 15
- assigning ranks
- generating readable reasons
- explaining individual gateways
- generating all 8 scored weeks
- writing `predictions.csv`

### `api.py`

Responsible for:

- HTTP endpoints
- input validation
- status codes
- health checks
- telemetry caching
- rerun behaviour

This separation means the ranking implementation can be replaced without changing the API contract, which directly supports the Software Development requirement that ranking can be swapped without changing the API. :contentReference[oaicite:1]{index=1}

---

## Ranking Method

The current implementation intentionally preserves the supplied 3-sigma baseline.

For each gateway and prediction Monday:

```text
Previous 28 days
        |
        v
Calculate mean + standard deviation
        |
        v
Look at most recent 7 days
        |
        v
Current value > mean + 3 × std?
        |
       Yes
        |
        v
Count anomaly breach
        |
        v
Rank gateways
```

The metrics used are:

```text
offline_duration_sec
disconnection_cnt
reboot_cnt
```

The purpose of this submission is not to replace the supplied baseline with an unnecessarily complex model, but to turn it into a maintainable, testable software service.

---

## Running Without Docker

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the API:

```bash
python -m uvicorn src.api:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

---

## Running With Docker

The recommended way to run the project is:

```bash
docker compose up --build
```

The Docker configuration:

- builds the Python environment
- installs dependencies
- starts the FastAPI service
- exposes port `8000`
- mounts challenge data from `./data`
- does not copy challenge data into the Docker image
- mounts `predictions.csv` so reruns update the host file

The data directory is mounted read-only:

```text
./data -> /app/data
```

This follows the challenge requirement to mount the supplied data rather than copying it into the image. :contentReference[oaicite:2]{index=2}

---

## Generate Predictions

### Through the API

Start the application and call:

```http
POST /run
```

### Using the supplied baseline directly

```bash
python baseline_3sigma.py --data data --out predictions.csv
```

---

## Validate the Submission

Run the supplied validator:

```bash
python validate_submission.py predictions.csv
```

Expected output:

```text
predictions.csv: OK
15 ranked gateways for each of 8 weeks, 2026-02-02 to 2026-03-23
```

The validator checks the required submission format.

---

## Tests

Run the complete automated test suite:

```bash
python -m pytest -v
```

Current development result:

```text
13 passed
```

The test suite covers:

- gateway anomaly ranking
- future-data leakage prevention
- recommendation count
- ranks from 1 to 15
- required output columns
- non-empty reasons
- API health behaviour
- weekly recommendation API
- invalid non-Monday input
- gateway explanation
- unknown gateway handling
- fresh telemetry reload regression
- full end-to-end prediction generation
- validation using the supplied LPDG validator

---

## End-to-End Test

The end-to-end test runs:

```text
Real telemetry
      |
      v
Data loading
      |
      v
Ranking
      |
      v
Service
      |
      v
8 weeks of recommendations
      |
      v
Temporary predictions.csv
      |
      v
LPDG validate_submission.py
      |
      v
PASS
```

This confirms that the complete application works rather than testing only individual functions.

---

## Regression Test From a Development Bug

Telemetry is cached in memory because repeatedly loading more than one million rows for normal API requests would add unnecessary I/O and latency.

During development I identified a problem with this design:

```text
Old telemetry
     |
     v
Cached in memory
     |
New data arrives
     |
     v
POST /run
```

Without cache invalidation, `/run` could potentially reuse stale telemetry.

The implementation therefore calls:

```python
get_telemetry.cache_clear()
```

before rerunning predictions.

A regression test verifies that fresh telemetry is loaded and passed to prediction generation after `/run`.

---

## Error Handling

The API deliberately handles common failure cases.

Examples include:

- telemetry directory missing
- telemetry dataset empty
- invalid timestamps
- missing gateway IDs
- unsupported prediction dates
- prediction date that is not a Monday
- gateway that does not exist
- insufficient historical telemetry

Failures return clear messages rather than silently generating potentially incorrect recommendations.

---

## Data Handling

The challenge data is intentionally excluded from Git using:

```text
data/
```

in `.gitignore`.

The application expects data to be placed in:

```text
./data
```

The supplied challenge data is never copied into the Docker image or committed to the repository.

---

## Design Decisions

Five important implementation decisions and the alternatives considered are documented in:

```text
DECISIONS.md
```

These include:

- retaining the supplied 3-sigma baseline
- preventing future-data leakage
- separating application layers
- caching telemetry while invalidating it on reruns
- selecting Software Development for Part 2

---

## Limitations

Known limitations and what I would improve with another two weeks are documented in:

```text
LIMITATIONS.md
```

The current system should be treated as a **field-visit prioritisation tool**, not proof that a gateway is definitely broken.

---

## AI Usage

AI-assisted development is documented transparently in:

```text
AI-USAGE.md
```

This includes:

- what AI was used for
- what was manually verified
- an AI-generated testing mistake that was identified
- how the test was improved
- how AI suggestions were reviewed rather than accepted automatically

---

## Part 2 Focus

I selected:

```text
Software Development
```

The goal of Part 2 is to demonstrate that the supplied ranking logic can be turned into software another developer could realistically pick up, run, test, understand and modify.

The implementation therefore focuses on:

- clean separation of responsibilities
- HTTP API design
- meaningful failure handling
- reproducibility
- automated testing
- end-to-end testing
- Docker-based startup
- documentation
- maintainability