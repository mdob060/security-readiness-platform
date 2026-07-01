import re
import subprocess


def get_jail_status(jail: str = "dira-auth") -> dict:
    try:
        proc = subprocess.run(
            ["fail2ban-client", "status", jail], capture_output=True, text=True, timeout=10
        )
    except FileNotFoundError:
        return {
            "jail": jail, "currently_failed": 0, "total_failed": 0,
            "currently_banned": 0, "total_banned": 0, "banned_ips": [],
        }

    output = proc.stdout
    def _int(pattern: str) -> int:
        m = re.search(pattern, output)
        return int(m.group(1)) if m else 0

    banned_line = re.search(r"Banned IP list:\s*(.*)", output)
    banned_ips = banned_line.group(1).split() if banned_line else []

    return {
        "jail": jail,
        "currently_failed": _int(r"Currently failed:\s*(\d+)"),
        "total_failed": _int(r"Total failed:\s*(\d+)"),
        "currently_banned": _int(r"Currently banned:\s*(\d+)"),
        "total_banned": _int(r"Total banned:\s*(\d+)"),
        "banned_ips": banned_ips,
    }
