"""
Hikvision ISUP Bridge - Configuration
Reads environment variables for service configuration.
"""
import os


class Settings:
    # ISUP Server
    ISUP_LISTEN_IP: str = os.getenv("ISUP_LISTEN_IP", "0.0.0.0")
    ISUP_LISTEN_PORT: int = int(os.getenv("ISUP_LISTEN_PORT", "7660"))

    # Hikvision Device
    HIKVISION_HOST: str = os.getenv("HIKVISION_HOST", "10.0.0.199")
    HIKVISION_PORT: int = int(os.getenv("HIKVISION_PORT", "8000"))
    HIKVISION_USER: str = os.getenv("HIKVISION_USER", "admin")
    HIKVISION_PASSWORD: str = os.getenv("HIKVISION_PASSWORD", "")

    # Hikvision SDK path
    SDK_LIB_PATH: str = os.getenv("SDK_LIB_PATH", "/app/sdk/libhcnetsdk.so")

    # Exousia API
    EXOUSIA_API_URL: str = os.getenv("EXOUSIA_API_URL", "http://exousia-backend:8000")
    EXOUSIA_API_TOKEN: str = os.getenv("EXOUSIA_API_TOKEN", "")

    # Bridge API
    BRIDGE_PORT: int = int(os.getenv("BRIDGE_PORT", "9500"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
