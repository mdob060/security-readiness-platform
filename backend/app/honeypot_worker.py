"""Standalone honeypot listener process (systemd: dira-honeypot.service).

Kept separate from the main API process so honeypot listeners survive API
restarts/deploys. Disable the embedded honeypots (ENABLE_EMBEDDED_HONEYPOTS=false)
on the main API process when this service is used.
"""
import logging
import time

from app.services.honeypot_listener import start_honeypots

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("dira.honeypot_worker")


def main() -> None:
    logger.info("Dir'a honeypot worker starting")
    start_honeypots()
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
