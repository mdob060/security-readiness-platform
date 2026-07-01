"""Real subprocess adapters around the integrated security tools.

Every builder returns a plain argv list (never a shell string), so user
input can never be interpreted as shell syntax. Targets passed in here must
already have gone through `services.scan_targets.validate_and_check_scope`.
"""
import subprocess
from pathlib import Path

WORDLIST_PATH = str(Path(__file__).parent / "wordlists" / "common.txt")

OFFENSIVE_TOOLS = {
    "nmap",
    "nuclei",
    "sqlmap",
    "gobuster",
    "ffuf",
    "whatweb",
    "amass",
    "hydra",
    "wpscan",
    "dnsrecon",
    "nikto",
    "masscan",
}

DEFENSIVE_TOOLS = {"lynis", "clamscan", "rkhunter", "chkrootkit", "fail2ban-client"}

VALID_HYDRA_SERVICES = {"ssh", "ftp", "http-get", "mysql", "telnet"}


def _build_offensive_argv(tool: str, target: str, service: str | None) -> list[str]:
    if tool == "nmap":
        return ["nmap", "-T4", "-sV", "-Pn", "--top-ports", "100", target]
    if tool == "nuclei":
        url = target if target.startswith(("http://", "https://")) else f"http://{target}"
        return [
            "nuclei", "-u", url, "-silent", "-duc", "-nc", "-timeout", "10",
            "-severity", "info,low,medium,high,critical",
        ]
    if tool == "sqlmap":
        url = target if target.startswith(("http://", "https://")) else f"http://{target}"
        return ["sqlmap", "-u", url, "--batch", "--level=1", "--risk=1", "--random-agent"]
    if tool == "gobuster":
        url = target if target.startswith(("http://", "https://")) else f"http://{target}"
        return ["gobuster", "dir", "-u", url, "-w", WORDLIST_PATH, "-q", "-t", "10", "--timeout", "5s"]
    if tool == "ffuf":
        url = target if target.startswith(("http://", "https://")) else f"http://{target}"
        return ["ffuf", "-u", f"{url}/FUZZ", "-w", WORDLIST_PATH, "-s", "-timeout", "5"]
    if tool == "whatweb":
        return ["whatweb", "--no-errors", target]
    if tool == "amass":
        return ["amass", "enum", "-passive", "-d", target, "-timeout", "2"]
    if tool == "hydra":
        svc = service if service in VALID_HYDRA_SERVICES else "ssh"
        return ["hydra", "-l", "testuser", "-P", WORDLIST_PATH, "-t", "4", "-f", f"{svc}://{target}"]
    if tool == "wpscan":
        url = target if target.startswith(("http://", "https://")) else f"http://{target}"
        return ["wpscan", "--url", url, "--no-banner", "--random-user-agent"]
    if tool == "dnsrecon":
        return ["dnsrecon", "-d", target]
    if tool == "nikto":
        return ["nikto", "-h", target, "-timeout", "10"]
    if tool == "masscan":
        return ["masscan", target, "-p1-1000", "--rate", "1000"]
    raise ValueError(f"Unknown offensive tool: {tool}")


def _build_defensive_argv(tool: str) -> list[str]:
    if tool == "lynis":
        return ["lynis", "audit", "system", "--quick", "--quiet", "--no-colors"]
    if tool == "clamscan":
        return [
            "clamscan",
            "-r",
            "-d",
            "/var/lib/dira/clamav-custom-db/dira-custom.hdb",
            "/var/lib/dira/clamav-sample",
            "/home",
        ]
    if tool == "rkhunter":
        return ["rkhunter", "--check", "--skip-keypress", "--no-colors", "--report-warnings-only"]
    if tool == "chkrootkit":
        return ["chkrootkit"]
    if tool == "fail2ban-client":
        return ["fail2ban-client", "status"]
    raise ValueError(f"Unknown defensive tool: {tool}")


def _run(argv: list[str], timeout: int) -> tuple[int, str]:
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired as exc:
        partial = (exc.stdout or "") + (exc.stderr or "")
        return -1, f"[scan timed out after {timeout}s]\n{partial}"
    except FileNotFoundError:
        return -127, f"Tool binary '{argv[0]}' is not installed on this host."


def run_offensive_tool(tool: str, target: str, timeout: int, service: str | None = None) -> tuple[int, str, list[str]]:
    argv = _build_offensive_argv(tool, target, service)
    rc, output = _run(argv, timeout)
    return rc, output, argv


def run_defensive_tool(tool: str, timeout: int) -> tuple[int, str, list[str]]:
    argv = _build_defensive_argv(tool)
    rc, output = _run(argv, timeout)
    return rc, output, argv
