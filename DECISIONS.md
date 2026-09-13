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