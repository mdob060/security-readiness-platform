from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Dir'a Security Operations Platform"
    environment: str = "development"

    database_url: str = "postgresql+psycopg://dira:dira_dev_password_change_me@localhost:5432/dira"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION_use_a_long_random_value"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8

    failed_login_max_attempts: int = 5
    failed_login_lockout_minutes: int = 5

    max_request_body_bytes: int = 5 * 1024 * 1024  # 5 MB

    cors_origins: list[str] = ["http://localhost:3000"]

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    scan_workspace_dir: str = "/tmp/dira-scans"
    backup_dir: str = "/var/backups/dira"

    allow_public_scan_targets: bool = False
    scan_timeout_seconds: int = 300


settings = Settings()
