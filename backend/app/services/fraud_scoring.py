from datetime import datetime, timezone


def score_transaction(account_from: str, account_to: str, amount: float, channel: str) -> tuple[float, list[str]]:
    score = 0.0
    reasons = []

    if amount > 10000:
        score += 40
        reasons.append(f"High amount ({amount})")
    if channel == "wire" and amount > 5000:
        score += 20
        reasons.append("Large wire transfer")
    if account_from == account_to:
        score += 100
        reasons.append("Source and destination account are identical")
    hour = datetime.now(timezone.utc).hour
    if hour < 5:
        score += 15
        reasons.append("Transaction occurred during low-activity hours")

    return min(score, 100.0), reasons
