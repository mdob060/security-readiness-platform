"""Standalone SOC detection-loop process (systemd: dira-monitor.service).

Runs independently of the main API process so it keeps monitoring even if
the API is restarted, matching the platform's "separate systemd services"
architecture. When running the API via `uvicorn` directly for local
development, set ENABLE_EMBEDDED_SCHEDULER=true instead and skip this
process entirely.
"""
import logging
import time

from app.services.detection_engine import run_detection_cycle

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("dira.monitor_worker")

CYCLE_SECONDS = 10


def main() -> None:
    logger.info("Dir'a SOC monitor worker starting (cycle=%ss)", CYCLE_SECONDS)
    while True:
        run_detection_cycle()
        time.sleep(CYCLE_SECONDS)


if __name__ == "__main__":
    main()
