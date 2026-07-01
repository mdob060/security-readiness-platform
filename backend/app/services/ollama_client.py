"""Client for the local, fully-sovereign AI Brain.

Talks to a local Ollama instance over HTTP (never an external API, matching
the platform's "no external connection" design). If Ollama is not reachable
on this host, falls back to a small local rule-based security assistant so
the feature still works end-to-end without ever calling out to the internet.
"""
import httpx

from app.core.config import settings

_FALLBACK_KB = [
    (["sql injection", "sqli"], "SQL Injection is prevented by using parameterized queries/prepared statements, "
     "input validation, and least-privilege DB accounts. Run 'sqlmap' scans only against targets approved in Scan Scope."),
    (["xss", "cross-site scripting"], "XSS is mitigated with output encoding, a strict Content-Security-Policy, "
     "and HttpOnly/Secure cookies. This platform sets CSP headers on every response by default."),
    (["brute force", "بروت فورس", "failed login"], "Brute-force attempts are detected automatically by the SOC "
     "detection engine (5+ failed logins in 5 minutes) and the account lockout policy locks the account for 5 minutes."),
    (["fail2ban"], "fail2ban here watches /var/log/dira/auth.log via the dira-auth jail and auto-bans source IPs "
     "with iptables after repeated failed logins."),
    (["pci", "pci-dss", "بطاقات"], "PCI-DSS compliance here is computed live from firewall rule presence, TLS "
     "certificate presence, ClamAV signature DB status, and audit log activity -- see the PCI-DSS page."),
    (["honeypot", "مصيدة"], "Honeypot listeners run on ports 2121 (ftp), 2222 (ssh), 2323 (telnet), 8081 (http), "
     "and 3307 (mysql). Any connection is logged with source IP and a payload sample."),
]


def _fallback_answer(message: str) -> str:
    lowered = message.lower()
    for keywords, answer in _FALLBACK_KB:
        if any(kw in lowered for kw in keywords):
            return answer
    return (
        "Local AI Brain (offline fallback -- Ollama is not reachable on this host): "
        "I can answer questions about SOC alerts, incidents, scan results, and compliance status "
        "using data already in this platform. Try asking about a specific alert, tool, or control."
    )


def generate_response(message: str, history: list[dict[str, str]] | None = None) -> tuple[str, bool]:
    """Returns (answer, used_local_llm)."""
    messages = (history or []) + [{"role": "user", "content": message}]
    try:
        with httpx.Client(base_url=settings.ollama_base_url, timeout=15.0) as client:
            resp = client.post(
                "/api/chat",
                json={"model": settings.ollama_model, "messages": messages, "stream": False},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"], True
    except (httpx.HTTPError, KeyError, ValueError):
        return _fallback_answer(message), False
