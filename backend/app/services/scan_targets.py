"""Target syntax validation and network-scope enforcement for the Scan Scope gate.

Any target must first be validated here before an offensive tool adapter ever
sees it. Two independent checks are enforced:

1. Syntax: the target must look like a bare hostname/IP/CIDR block and must
   not start with '-' (which could otherwise be interpreted as a tool flag
   when passed as an argv element).
2. Network scope: unless `settings.allow_public_scan_targets` is explicitly
   enabled by a platform administrator, only private/loopback ranges may be
   scanned. This is a safety net in addition to (not a replacement for) the
   human approval workflow in Scan Scope -- real external engagements always
   require both the config flag and an approved ScopeTarget record.
"""
import ipaddress
import re
import socket

from app.core.config import settings

_TARGET_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.\-_:/]*[A-Za-z0-9])?$")


class TargetValidationError(ValueError):
    pass


def validate_target_syntax(target: str) -> str:
    target = target.strip()
    if not target or len(target) > 253:
        raise TargetValidationError("Target must be a non-empty string of reasonable length")
    if target.startswith("-"):
        raise TargetValidationError("Target must not start with '-'")
    if not _TARGET_RE.match(target):
        raise TargetValidationError("Target contains invalid characters")
    return target


def _is_private_host(host: str) -> bool:
    if host in ("localhost",):
        return True
    try:
        ip = ipaddress.ip_network(host, strict=False)
        return ip.is_private or ip.is_loopback
    except ValueError:
        pass
    try:
        resolved = socket.gethostbyname(host)
        ip = ipaddress.ip_address(resolved)
        return ip.is_private or ip.is_loopback
    except (socket.gaierror, ValueError):
        return False


def _strip_port(host: str) -> str:
    """Strips a trailing ':<port>' (e.g. '127.0.0.1:8000' -> '127.0.0.1'),
    while leaving bare IPv6 addresses (which contain multiple colons) alone."""
    if host.count(":") == 1:
        candidate_host, _, candidate_port = host.rpartition(":")
        if candidate_port.isdigit():
            return candidate_host
    return host


def enforce_network_scope(target: str) -> None:
    if settings.allow_public_scan_targets:
        return
    host = _strip_port(target.split("/")[0])
    if not _is_private_host(host):
        raise TargetValidationError(
            "This platform is configured to only scan private/localhost targets. "
            "An administrator must enable ALLOW_PUBLIC_SCAN_TARGETS after confirming "
            "written authorization for external engagements."
        )


def validate_and_check_scope(target: str) -> str:
    target = validate_target_syntax(target)
    enforce_network_scope(target)
    return target
