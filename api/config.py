from enum import Enum
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class EnvironmentEnum(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

class IngestionSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="P7_",
        case_sensitive=False,
        extra="forbid"
    )

    ENVIRONMENT: EnvironmentEnum = EnvironmentEnum.DEVELOPMENT
    API_TITLE: str = "Project 07 Red Ingestion API"
    API_VERSION: str = "1.0.0"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    API_KEY_REQUIRED: bool = False
    API_KEY: str = "dev-insecure-test-key"
    MAX_BATCH_SIZE: int = 100
    STORAGE_TYPE: str = "memory"
    WATCHDOG_AUTO_EVALUATE: bool = True
    WATCHDOG_INTERVAL_SEC: float = 1.0

    @model_validator(mode="after")
    def enforce_production_security(self) -> "IngestionSettings":
        if self.ENVIRONMENT == EnvironmentEnum.TESTING:
            if "WATCHDOG_AUTO_EVALUATE" not in self.model_fields_set:
                self.WATCHDOG_AUTO_EVALUATE = False

        if self.ENVIRONMENT == EnvironmentEnum.PRODUCTION:
            if not self.API_KEY_REQUIRED:
                raise ValueError("In PRODUCTION, API_KEY_REQUIRED must be set to True.")
            if not self.API_KEY or self.API_KEY == "dev-insecure-test-key":
                raise ValueError(
                    "In PRODUCTION, a secure, non-default P7_API_KEY must be explicitly configured."
                )
        return self

settings = IngestionSettings()
