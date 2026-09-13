# Decisions

## 1. Keep the supplied 3-sigma method as the ranking baseline

### Decision
I kept the supplied 3-sigma approach as the core ranking method for the challenge submission.

For each Monday, the service uses the previous 28 days of telemetry to establish each gateway's normal behaviour, then checks the most recent 7 days for unusual values in:

- offline duration
- disconnection count
- reboot count

### Alternative considered
Replace the baseline immediately with a machine-learning model or a more complex scoring algorithm.

### Why I did not choose it
My Part 2 focus is Software Development rather than Machine Learning. The supplied baseline already gives a valid and understandable ranking method, so I chose to spend more time making the service reliable, testable and easy for another developer to extend.

This also reduces the risk of introducing an unvalidated ranking change while building the software layer.

---

## 2. Never use telemetry from or after the prediction Monday

### Decision
All ranking calculations use telemetry strictly before `week_start`.

For example, a recommendation for 2026-02-02 cannot use telemetry recorded on or after 2026-02-02.

### Alternative considered
Calculate historical statistics using the complete telemetry dataset.

### Why I did not choose it
Using future information would create look-ahead leakage and would make historical results unrealistically strong.

The service is intended to behave as it would have behaved on that Monday with only the information available at that time.

A regression test verifies that adding future telemetry does not change an earlier week's ranking.

---

## 3. Separate data loading, ranking, business logic and API handling

### Decision
I separated the application into:

- `data_loader.py` — reads and validates telemetry
- `ranking.py` — calculates gateway rankings
- `service.py` — builds recommendations and explanations
- `api.py` — exposes the HTTP interface

### Alternative considered
Put data loading, ranking and API logic in a single Python file or directly inside FastAPI route handlers.

### Why I did not choose it
A single-file design would be quicker initially, but harder to test and harder to modify.

With this structure, the ranking method can be replaced later without changing the API contract. It also makes unit testing and live changes easier.

---

## 4. Cache telemetry for normal API calls, but invalidate the cache on rerun

### Decision
The API loads telemetry once and reuses it for normal requests to avoid repeatedly reading more than one million telemetry rows.

When `POST /run` is called, the cache is cleared before the data is loaded again.

### Alternative considered
Reload the complete telemetry dataset on every API request.

### Why I did not choose it
Reloading the same large dataset on every request would add unnecessary latency and I/O.

However, caching introduced a stale-data risk when new telemetry arrived. I noticed this during development and changed `/run` to invalidate the cache before regenerating predictions.

I added a regression test to make sure a rerun uses fresh data instead of the cached copy.

---

## 5. Choose Software Development for Part 2

### Decision
I chose Software Development as my Part 2 area.

I wrapped the ranking logic in a FastAPI service with:

- weekly recommendation endpoint
- individual gateway explanation endpoint
- rerun endpoint
- health endpoint
- validation and error handling
- unit, API and end-to-end tests
- Docker-based one-command startup

### Alternative considered
Choose Machine Learning and attempt to beat the supplied baseline, or choose Data Engineering and focus primarily on incremental pipeline processing.

### Why I did not choose it
I wanted the submission to demonstrate production-oriented software engineering: clean boundaries, testability, failure handling, reproducibility and an interface another developer can immediately use.

I considered that a stronger and more defensible demonstration of my chosen area than adding a more complex prediction model without enough time to validate it properly.
---

## Additional judgement on the visit decision

The submission format requires exactly 15 ranked gateways for each scored week, so the generated `predictions.csv` always contains 15 recommendations per Monday.

However, I would not treat 15 as a mandatory operational target in a real deployment.

A field visit costs €380 when nothing is wrong, while leaving a genuinely broken gateway unvisited costs €600 for each week it remains broken. This means the operational decision should eventually depend on expected risk and cost, rather than filling all 15 visit slots automatically.

For this challenge I kept the supplied 3-sigma baseline because my Part 2 focus is Software Development. I did not introduce an unvalidated cost threshold simply to change the ranking.

In a production version, I would evaluate a threshold where a gateway is recommended only when the expected cost of leaving it unvisited is greater than the expected cost of sending an engineer.

This could mean recommending fewer than 15 gateways in a genuinely healthy week, while still respecting 15 as the maximum available field capacity.
---

## Additional Software Development Decisions

### Handling silent or incomplete telemetry

A gateway can have historical telemetry but no rows in the most recent seven days.

I do not automatically classify silence as a fault because the data does not distinguish between a physical gateway failure and missing telemetry.

Instead, the ranking keeps the gateway visible and reports:

- recent telemetry hours
- recent coverage ratio
- whether recent telemetry is incomplete

A completely silent gateway therefore receives an anomaly score of zero from the supplied 3-sigma logic, but it does not silently disappear from the ranking.

Alternative considered:
Treat every missing hour as a fault.

Why I rejected it:
That would make a strong assumption about the cause of missing telemetry that the supplied data cannot prove.

### Full regeneration on POST /run

`POST /run` performs a full regeneration of the eight scored weeks instead of incrementally updating only one period.

I chose full regeneration because the current dataset is small enough for this to complete quickly, while the simpler implementation is easier to reason about, test and reproduce.

Before rerunning, the telemetry cache is cleared so newly mounted data is read without restarting the service.

The new predictions are written to a temporary file first and only replace `predictions.csv` after the write succeeds.

This avoids leaving a partially written output file if the rerun fails.

Alternative considered:
Incrementally update only the newest period.

Why I rejected it:
Incremental state would add more complexity around cached results, repeated calls and partial failures without providing meaningful value at the current data size.