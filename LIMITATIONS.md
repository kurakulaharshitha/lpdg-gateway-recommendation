# Limitations

## What the current service cannot do

### 1. It detects unusual behaviour, but not the root cause

The current ranking identifies gateways whose recent telemetry is unusual compared with their own previous 28-day behaviour.

It cannot determine whether the underlying cause is:

- a hardware fault
- power instability
- backhaul/network problems
- firmware behaviour
- antenna or signal issues

A field engineer is still required to determine the actual cause.

---

### 2. The ranking uses only three telemetry metrics

The current baseline uses:

- offline duration
- disconnection count
- reboot count

The dataset contains additional signals such as signal quality, memory, CPU/load information, packet errors and meter-read success.

These may provide useful evidence that the current ranking does not use.

---

### 3. The score does not directly model business impact

The current score measures anomaly breaches.

It does not currently increase priority because one gateway serves significantly more meters than another.

For example, two gateways may have the same anomaly score even if one affects 50 meters and another affects 800 meters.

---

### 4. The €380 and €600 costs are not directly optimised

The current software keeps the supplied baseline ranking method.

It does not explicitly calculate the expected cost of:

- sending an engineer to a healthy gateway
- leaving a failed gateway unvisited

A cost-aware decision rule may produce a better operational ranking.

---

### 5. A zero historical standard deviation can hide a new anomaly

If a metric was completely constant during the historical baseline period, its standard deviation can be zero.

The supplied baseline avoids division or threshold problems by treating that case as non-flagging.

This means a gateway that historically never rebooted, for example, may not be flagged by that metric when it suddenly begins rebooting.

---

### 6. The explanation is useful but still simple

The API currently explains:

- the score
- ranking
- whether the gateway is selected
- the first abnormal signal

It does not yet provide a detailed breakdown of every contributing metric or show the recent trend that produced the ranking.

---

## What I would improve with another two weeks

With two additional weeks I would:

1. Compare the baseline ranking against field-visit outcomes and engineer reviews.
2. Add meter-read success as a business-impact signal.
3. Use the number of meters behind each gateway as a ranking tie-breaker or impact factor.
4. Evaluate a cost-aware threshold using the €380 false-visit cost and €600 missed-failure cost.
5. Improve handling of zero-variance historical metrics.
6. Add richer gateway explanations showing per-metric anomaly counts and recent trends.
7. Add structured application logging and operational metrics.
8. Test the service against a newly arrived month of telemetry to confirm it behaves correctly on unseen data.

## Overall limitation

The current system should be treated as a prioritisation service, not as proof that a gateway is broken.

Its purpose is to help the field team decide where to look first.