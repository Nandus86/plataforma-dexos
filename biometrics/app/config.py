"""
Hikvision ISUP Bridge - Configuration
Reads environment variables for service configuration.
"""
import os


class Settings:
    # ISUP Server
    ISUP_LISTEN_IP: str = os.getenv("ISUP_LISTEN_IP", "0.0.0.0")
    ISUP_LISTEN_PORT: int = int(os.getenv("ISUP_LISTEN_PORT", "7660"))

    # Hikvision SDK path
    SDK_LIB_PATH: str = os.getenv("SDK_LIB_PATH", "/app/sdk/libhcnetsdk.so")

    # Exousia API
    EXOUSIA_API_URL: str = os.getenv("EXOUSIA_API_URL", "http://exousia-backend:8000/api/v1")
    EXOUSIA_API_TOKEN: str = os.getenv("EXOUSIA_API_TOKEN", "")

    # Bridge API
    BRIDGE_PORT: int = int(os.getenv("BRIDGE_PORT", "9500"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
