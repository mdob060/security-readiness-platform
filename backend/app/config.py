"""
NATIONAL CYBER DEFENSE PROTOTYPE C+
Configuration Settings
"""

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "NATIONAL CYBER DEFENSE PROTOTYPE C+"
    version: str = "1.0.0"
    classification: str = "PROTOTYPE"
    debug: bool = False

    # Threat Intel
    ioc_retention_days: int = 90
    feed_refresh_interval: int = 3600  # seconds

    # Automated Response
    auto_response_enabled: bool = True
    max_concurrent_playbooks: int = 10
    playbook_timeout: int = 300  # seconds

    # MITRE ATT&CK
    mitre_attack_version: str = "v14.1"


settings = Settings()
