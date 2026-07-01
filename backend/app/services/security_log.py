"""Writes failed-login events to a plain-text log that fail2ban's dira-auth
jail tails (see infra/fail2ban/). This is what lets fail2ban auto-block
repeat offenders, independent of the account-lockout logic in the DB.
"""
from datetime import datetime, timezone

AUTH_LOG_PATH = "/var/log/dira/auth.log"


def log_failed_login(username: str, ip_address: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} Failed login for user={username} from {ip_address}\n"
    try:
        with open(AUTH_LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        pass
