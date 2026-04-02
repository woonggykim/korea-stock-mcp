from __future__ import annotations

import httpx

from korea_stock_mcp.adapters.base import MarketDataAdapter
from korea_stock_mcp.config import Settings
from korea_stock_mcp.mock_data import MOCK_PRICES, MOCK_SECURITIES
from korea_stock_mcp.models import DisclosureItem, FinancialMetric, PriceBar, SecurityProfile, SourceMeta


class KrxAdapter(MarketDataAdapter):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def search_security(self, query: str) -> list[SecurityProfile]:
        matches: list[SecurityProfile] = []
        for profile in MOCK_SECURITIES.values():
            if query in profile.identifier.ticker or query.lower() in profile.identifier.name_ko.lower():
                matches.append(self._with_source(profile))
        return matches

    async def get_security_profile(self, ticker: str) -> SecurityProfile | None:
        profile = MOCK_SECURITIES.get(ticker)
        return self._with_source(profile) if profile else None

    async def get_price_history(self, ticker: str, limit: int = 60) -> list[PriceBar]:
        if not self.settings.use_mock_data and self.settings.krx_api_key:
            history = await self._get_price_history_live(ticker, limit)
            if history:
                return history
        return list(MOCK_PRICES.get(ticker, []))[-limit:]

    async def get_financial_metrics(self, ticker: str) -> list[FinancialMetric]:
        return []

    async def get_recent_disclosures(self, ticker: str, limit: int = 20) -> list[DisclosureItem]:
        return []

    def _with_source(self, profile: SecurityProfile) -> SecurityProfile:
        clone = profile.model_copy(deep=True)
        clone.source_meta.append(
            SourceMeta(source="krx", latency_class="end_of_day", note="Mock KRX adapter; replace with official API integration.")
        )
        return clone

    async def _get_price_history_live(self, ticker: str, limit: int) -> list[PriceBar]:
        # KRX Open API access is approval-driven and product-specific.
        # If a compatible endpoint is configured, this method can hydrate price history
        # from that endpoint; otherwise the adapter falls back to mock/public data.
        path = "/placeholder"
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(
                    f"{self.settings.krx_api_base_url}{path}",
                    params={"ticker": ticker, "limit": limit},
                    headers={"Authorization": self.settings.krx_api_key},
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError):
            return []

        items = payload.get("items", [])
        history: list[PriceBar] = []
        for item in items[-limit:]:
            close = self._to_int(item.get("close"))
            if close is None:
                continue
            history.append(
                PriceBar(
                    date=item.get("date", ""),
                    open=self._to_int(item.get("open")),
                    high=self._to_int(item.get("high")),
                    low=self._to_int(item.get("low")),
                    close=close,
                    volume=self._to_int(item.get("volume")),
                    turnover=self._to_int(item.get("turnover")),
                )
            )
        return history

    def _to_int(self, value: str | int | None) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(str(value).replace(",", ""))
        except ValueError:
            return None
