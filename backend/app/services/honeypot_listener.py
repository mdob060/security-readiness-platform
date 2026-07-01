"""Real TCP honeypot listeners.

Each configured port runs an actual socket server. Any inbound connection is
logged (source IP/port, the fake service it hit, and up to 256 bytes of
whatever the connecting client sends) before the connection is closed. This
is genuine network-level capture, not simulated data.
"""
import logging
import socketserver
import threading

from app.db.base import SessionLocal
from app.models.monitoring import HoneypotEvent, SecurityEvent

logger = logging.getLogger("dira.honeypot")

# port -> fake service banner
HONEYPOT_PORTS = {
    2121: ("ftp", "220 ProFTPD 1.3.5 Server ready.\r\n"),
    2222: ("ssh", "SSH-2.0-OpenSSH_7.4\r\n"),
    2323: ("telnet", "\r\nlogin: "),
    8081: ("http", "HTTP/1.1 200 OK\r\nServer: Apache/2.4.41\r\n\r\n"),
    3307: ("mysql", "\x4a\x00\x00\x00\x0a5.7.31\x00"),
}


class HoneypotHandler(socketserver.BaseRequestHandler):
    service_name = "unknown"
    banner = ""

    def handle(self) -> None:
        source_ip, source_port = self.client_address
        payload = b""
        try:
            if self.banner:
                self.request.sendall(self.banner.encode("utf-8", errors="ignore"))
            self.request.settimeout(2.0)
            payload = self.request.recv(256)
        except OSError:
            pass
        finally:
            try:
                self.request.close()
            except OSError:
                pass

        db = SessionLocal()
        try:
            db.add(
                HoneypotEvent(
                    listener_port=self.server.server_address[1],
                    service_name=self.service_name,
                    source_ip=source_ip,
                    source_port=source_port,
                    payload_sample=payload.decode("utf-8", errors="replace")[:256] if payload else None,
                )
            )
            db.add(
                SecurityEvent(
                    source="honeypot",
                    event_type=f"honeypot_{self.service_name}_connection",
                    source_ip=source_ip,
                    detail=f"Connection to {self.service_name} honeypot on port {self.server.server_address[1]}",
                )
            )
            db.commit()
        finally:
            db.close()


def _make_handler(service_name: str, banner: str):
    return type(f"Handler_{service_name}", (HoneypotHandler,), {"service_name": service_name, "banner": banner})


_servers: list[socketserver.ThreadingTCPServer] = []


def start_honeypots() -> None:
    for port, (service_name, banner) in HONEYPOT_PORTS.items():
        try:
            handler_cls = _make_handler(service_name, banner)
            server = socketserver.ThreadingTCPServer(("0.0.0.0", port), handler_cls)
            server.daemon_threads = True
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            _servers.append(server)
            logger.info("Honeypot listener started: %s on port %s", service_name, port)
        except OSError as exc:
            logger.warning("Could not bind honeypot port %s (%s): %s", port, service_name, exc)


def stop_honeypots() -> None:
    for server in _servers:
        server.shutdown()
        server.server_close()
    _servers.clear()
