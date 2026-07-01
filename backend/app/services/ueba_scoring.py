"""Online baseline/anomaly scoring for UEBA using Welford's running mean/variance."""
import json
import math


def update_baseline_and_score(baseline_json: str | None, value: float) -> tuple[str, float]:
    if baseline_json:
        baseline = json.loads(baseline_json)
    else:
        baseline = {"n": 0, "mean": 0.0, "m2": 0.0}

    n = baseline["n"] + 1
    delta = value - baseline["mean"]
    mean = baseline["mean"] + delta / n
    delta2 = value - mean
    m2 = baseline["m2"] + delta * delta2

    variance = m2 / n if n > 1 else 0.0
    std = math.sqrt(variance)

    anomaly_score = abs(value - mean) / std if std > 0 else 0.0

    new_baseline = json.dumps({"n": n, "mean": mean, "m2": m2})
    return new_baseline, round(min(anomaly_score, 10.0), 3)
