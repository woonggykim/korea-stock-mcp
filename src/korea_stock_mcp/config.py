from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    request_timeout_seconds: float = float(os.getenv("KOREA_STOCK_MCP_REQUEST_TIMEOUT_SECONDS", "15"))
    krx_api_key: str | None = os.getenv("KRX_API_KEY")
    krx_api_base_url: str = os.getenv("KRX_API_BASE_URL", "https://openapi.krx.co.kr")
    open_dart_api_key: str | None = os.getenv("OPEN_DART_API_KEY")
    open_dart_api_base_url: str = os.getenv("OPEN_DART_API_BASE_URL", "https://opendart.fss.or.kr/api")
    public_data_api_key: str | None = os.getenv("PUBLIC_DATA_API_KEY")
    public_data_api_base_url: str = os.getenv("PUBLIC_DATA_API_BASE_URL", "https://apis.data.go.kr/1160100/service")
    cache_url: str | None = os.getenv("KOREA_STOCK_MCP_CACHE_URL")
    db_url: str | None = os.getenv("KOREA_STOCK_MCP_DB_URL")
    use_mock_data: bool = os.getenv("KOREA_STOCK_MCP_USE_MOCK_DATA", "1") == "1"


def load_settings() -> Settings:
    return Settings()
