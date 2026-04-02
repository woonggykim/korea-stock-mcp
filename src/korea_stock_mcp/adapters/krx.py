from __future__ import annotations

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
