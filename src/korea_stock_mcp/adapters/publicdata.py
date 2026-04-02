from __future__ import annotations

from datetime import date, timedelta

import httpx

from korea_stock_mcp.adapters.base import MarketDataAdapter
from korea_stock_mcp.config import Settings
from korea_stock_mcp.mock_data import MOCK_PRICES, MOCK_SECURITIES
from korea_stock_mcp.models import DisclosureItem, FinancialMetric, MarketSnapshot, PriceBar, SecurityProfile, SourceMeta


class PublicDataAdapter(MarketDataAdapter):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def search_security(self, query: str) -> list[SecurityProfile]:
        if not self.settings.use_mock_data and self.settings.public_data_api_key:
            matches = await self._search_security_live(query)
            if matches:
                return matches

        matches: list[SecurityProfile] = []
        for profile in MOCK_SECURITIES.values():
            if query in profile.identifier.ticker or query.lower() in profile.identifier.name_ko.lower():
                matches.append(self._with_source(profile))
        return matches

    async def get_security_profile(self, ticker: str) -> SecurityProfile | None:
        if not self.settings.use_mock_data and self.settings.public_data_api_key:
            profile = await self._get_security_profile_live(ticker)
            if profile:
                return profile

        profile = MOCK_SECURITIES.get(ticker)
        return self._with_source(profile) if profile else None

    async def get_price_history(self, ticker: str, limit: int = 60) -> list[PriceBar]:
        if not self.settings.use_mock_data and self.settings.public_data_api_key:
            history = await self._get_price_history_live(ticker, limit)
            if history:
                return history
        return list(MOCK_PRICES.get(ticker, []))[-limit:]

    async def get_financial_metrics(self, ticker: str) -> list[FinancialMetric]:
        return []

    async def get_recent_disclosures(self, ticker: str, limit: int = 20) -> list[DisclosureItem]:
        return []

    async def get_market_snapshot(self, market: str) -> MarketSnapshot | None:
        if not self.settings.use_mock_data and self.settings.public_data_api_key:
            snapshot = await self._get_market_snapshot_live(market)
            if snapshot:
                return snapshot
        return None

    def _with_source(self, profile: SecurityProfile) -> SecurityProfile:
        clone = profile.model_copy(deep=True)
        clone.source_meta.append(
            SourceMeta(
                source="data_go_kr",
                latency_class="next_business_day",
                note="Mock public data adapter; replace with official data.go.kr integration.",
            )
        )
        return clone

    async def _search_security_live(self, query: str) -> list[SecurityProfile]:
        params = {"numOfRows": 5000 if not query else 20, "resultType": "json"}
        if query:
            if query.isdigit():
                params["likeSrtnCd"] = query
            else:
                params["likeItmsNm"] = query
        payload = await self._get_json("GetKrxListedInfoService/getItemInfo", params)
        items = self._extract_items(payload)
        return [self._item_to_profile(item) for item in items[:20]]

    async def _get_security_profile_live(self, ticker: str) -> SecurityProfile | None:
        payload = await self._get_json(
            "GetKrxListedInfoService/getItemInfo",
            {"resultType": "json", "likeSrtnCd": ticker, "numOfRows": 20},
        )
        for item in self._extract_items(payload):
            if item.get("srtnCd") == ticker:
                return self._item_to_profile(item)
        return None

    async def _get_price_history_live(self, ticker: str, limit: int) -> list[PriceBar]:
        today = date.today()
        start = today - timedelta(days=max(limit * 3, 40))
        payload = await self._get_json(
            "GetStockSecuritiesInfoService/getStockPriceInfo",
            {
                "resultType": "json",
                "likeSrtnCd": ticker,
                "beginBasDt": start.strftime("%Y%m%d"),
                "endBasDt": today.strftime("%Y%m%d"),
                "numOfRows": max(limit, 60),
            },
        )
        items = [item for item in self._extract_items(payload) if item.get("srtnCd") == ticker]
        items.sort(key=lambda item: item.get("basDt", ""))
        history: list[PriceBar] = []
        for item in items[-limit:]:
            close = self._to_int(item.get("clpr"))
            if close is None:
                continue
            history.append(
                PriceBar(
                    date=item.get("basDt", ""),
                    open=self._to_int(item.get("mkp")),
                    high=self._to_int(item.get("hipr")),
                    low=self._to_int(item.get("lopr")),
                    close=close,
                    volume=self._to_int(item.get("trqu")),
                    turnover=self._to_int(item.get("trPrc")),
                )
            )
        return history

    async def _get_market_snapshot_live(self, market: str) -> MarketSnapshot | None:
        today = date.today().strftime("%Y%m%d")
        payload = await self._get_json(
            "GetStockSecuritiesInfoService/getStockPriceInfo",
            {
                "resultType": "json",
                "basDt": today,
                "mrktCls": market,
                "numOfRows": 5000,
            },
        )
        items = self._extract_items(payload)
        if not items:
            return None

        advancers = 0
        decliners = 0
        unchanged = 0
        total_volume = 0
        total_turnover = 0
        movers: list[tuple[float, str]] = []

        for item in items:
            flt_rt = self._to_float(item.get("fltRt")) or 0.0
            if flt_rt > 0:
                advancers += 1
            elif flt_rt < 0:
                decliners += 1
            else:
                unchanged += 1
            total_volume += self._to_int(item.get("trqu")) or 0
            total_turnover += self._to_int(item.get("trPrc")) or 0
            movers.append((abs(flt_rt), item.get("srtnCd", "")))

        movers.sort(reverse=True)
        return MarketSnapshot(
            market=market,
            advancers=advancers,
            decliners=decliners,
            unchanged=unchanged,
            total_volume=total_volume,
            total_turnover=total_turnover,
            top_movers=[ticker for _, ticker in movers[:10] if ticker],
        )

    async def _get_json(self, path: str, params: dict[str, str | int]) -> dict | None:
        if not self.settings.public_data_api_key:
            return None

        request_params = {"serviceKey": self.settings.public_data_api_key, **params}
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(f"{self.settings.public_data_api_base_url}/{path}", params=request_params)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError):
            return None

    def _extract_items(self, payload: dict | None) -> list[dict]:
        if not payload:
            return []
        response = payload.get("response", {})
        body = response.get("body", {})
        items = body.get("items", {})
        item = items.get("item", [])
        if isinstance(item, dict):
            return [item]
        if isinstance(item, list):
            return item
        return []

    def _item_to_profile(self, item: dict) -> SecurityProfile:
        return SecurityProfile(
            identifier={
                "ticker": item.get("srtnCd", ""),
                "name_ko": item.get("itmsNm", ""),
                "market": item.get("mrktCtg") or item.get("mrktCls"),
                "isin": item.get("isinCd"),
            },
            source_meta=[
                SourceMeta(
                    source="data_go_kr",
                    latency_class="next_business_day",
                    as_of=item.get("basDt"),
                    note="Live listing/profile data from data.go.kr.",
                )
            ],
        )

    def _to_int(self, value: str | int | None) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(str(value).replace(",", ""))
        except ValueError:
            return None

    def _to_float(self, value: str | float | None) -> float | None:
        if value in (None, ""):
            return None
        try:
            return float(str(value).replace(",", ""))
        except ValueError:
            return None
