from __future__ import annotations

from statistics import mean

from korea_stock_mcp.adapters.dart import OpenDartAdapter
from korea_stock_mcp.adapters.krx import KrxAdapter
from korea_stock_mcp.adapters.publicdata import PublicDataAdapter
from korea_stock_mcp.config import Settings
from korea_stock_mcp.models import (
    DisclosureItem,
    FinancialMetric,
    InvestmentSummary,
    MarketSnapshot,
    PriceBar,
    ScreenCandidate,
    ScreenFilter,
    SecurityProfile,
    StockComparison,
)
from korea_stock_mcp.mock_data import MOCK_MARKET_SNAPSHOTS


class KoreaStockService:
    def __init__(self, settings: Settings) -> None:
        self.krx = KrxAdapter(settings)
        self.dart = OpenDartAdapter(settings)
        self.publicdata = PublicDataAdapter(settings)

    async def search_securities(self, query: str) -> list[SecurityProfile]:
        seen: dict[str, SecurityProfile] = {}
        for adapter in (self.krx, self.dart, self.publicdata):
            for profile in await adapter.search_security(query):
                existing = seen.get(profile.identifier.ticker)
                if existing:
                    existing.source_meta.extend(profile.source_meta)
                else:
                    seen[profile.identifier.ticker] = profile
        return list(seen.values())

    async def get_security_profile(self, ticker: str) -> SecurityProfile | None:
        base = await self.krx.get_security_profile(ticker)
        if base is None:
            base = await self.publicdata.get_security_profile(ticker)
        if base is None:
            return None

        dart_profile = await self.dart.get_security_profile(ticker)
        if dart_profile:
            base.source_meta.extend(dart_profile.source_meta)
            if not base.identifier.dart_corp_code:
                base.identifier.dart_corp_code = dart_profile.identifier.dart_corp_code
        return base

    async def get_price_history(self, ticker: str, limit: int = 60) -> list[PriceBar]:
        price_history = await self.krx.get_price_history(ticker, limit)
        if price_history:
            return price_history
        return await self.publicdata.get_price_history(ticker, limit)

    async def get_financial_metrics(self, ticker: str) -> list[FinancialMetric]:
        return await self.dart.get_financial_metrics(ticker)

    async def get_recent_disclosures(self, ticker: str, limit: int = 20) -> list[DisclosureItem]:
        return await self.dart.get_recent_disclosures(ticker, limit)

    async def get_market_snapshot(self, market: str) -> MarketSnapshot | None:
        return MOCK_MARKET_SNAPSHOTS.get(market.upper())

    async def compare_stocks(self, tickers: list[str]) -> StockComparison:
        profiles: list[SecurityProfile] = []
        latest_prices: dict[str, PriceBar] = {}
        latest_metrics: dict[str, FinancialMetric] = {}
        recent_disclosures: dict[str, list[DisclosureItem]] = {}

        for ticker in tickers:
            profile = await self.get_security_profile(ticker)
            if profile:
                profiles.append(profile)
            prices = await self.get_price_history(ticker, 1)
            if prices:
                latest_prices[ticker] = prices[-1]
            metrics = await self.get_financial_metrics(ticker)
            if metrics:
                latest_metrics[ticker] = metrics[-1]
            recent_disclosures[ticker] = await self.get_recent_disclosures(ticker, 5)

        return StockComparison(
            profiles=profiles,
            latest_prices=latest_prices,
            latest_metrics=latest_metrics,
            recent_disclosures=recent_disclosures,
        )

    async def summarize_investment_case(self, ticker: str) -> InvestmentSummary | None:
        profile = await self.get_security_profile(ticker)
        if profile is None:
            return None

        prices = await self.get_price_history(ticker, 20)
        metrics = await self.get_financial_metrics(ticker)
        disclosures = await self.get_recent_disclosures(ticker, 5)
        latest_metric = metrics[-1] if metrics else None

        if len(prices) >= 2:
            start = prices[0].close
            end = prices[-1].close
            performance = ((end - start) / start) * 100 if start else 0.0
            market_view = f"Recent price trend is {'positive' if performance >= 0 else 'negative'} with 20-period return of {performance:.1f}%."
        else:
            market_view = "Recent price history is limited."

        if latest_metric:
            financial_view = (
                f"Latest period {latest_metric.period} shows operating margin {latest_metric.operating_margin or 0:.1f}% "
                f"and ROE {latest_metric.roe or 0:.1f}%."
            )
        else:
            financial_view = "Financial metrics are not available yet."

        if disclosures:
            disclosure_view = f"{len(disclosures)} recent disclosures found, latest report: {disclosures[0].report_name}."
        else:
            disclosure_view = "No recent disclosures were found."

        risks = [
            "Mock-mode data is enabled until production APIs are wired.",
            "Public data endpoints may lag for some datasets versus market close or filing time.",
        ]

        source_notes = [
            "KRX is intended as the primary exchange data source.",
            "Open DART is intended for filings and financial statements.",
            "data.go.kr is intended for listed-stock reference data and public fallback coverage.",
        ]

        return InvestmentSummary(
            ticker=ticker,
            company_name=profile.identifier.name_ko,
            market_view=market_view,
            financial_view=financial_view,
            disclosure_view=disclosure_view,
            risks=risks,
            source_notes=source_notes,
        )

    async def screen_stocks(self, stock_filter: ScreenFilter | dict) -> list[ScreenCandidate]:
        if isinstance(stock_filter, dict):
            stock_filter = ScreenFilter.model_validate(stock_filter)

        universe = list((await self.search_securities("")).copy())
        candidates: list[ScreenCandidate] = []

        for profile in universe:
            if stock_filter.market and profile.identifier.market != stock_filter.market:
                continue

            prices = await self.get_price_history(profile.identifier.ticker, 20)
            if not prices:
                continue

            latest = prices[-1]
            avg_volume = mean(bar.volume or 0 for bar in prices)
            first_close = prices[0].close
            return_20d = ((latest.close - first_close) / first_close) * 100 if first_close else None

            metrics = await self.get_financial_metrics(profile.identifier.ticker)
            latest_metric = metrics[-1] if metrics else None
            disclosures = await self.get_recent_disclosures(profile.identifier.ticker, 30)

            if stock_filter.min_price and (latest.close < stock_filter.min_price):
                continue
            if stock_filter.max_price and (latest.close > stock_filter.max_price):
                continue
            if stock_filter.min_volume and avg_volume < stock_filter.min_volume:
                continue
            if stock_filter.min_return_20d is not None and (return_20d is None or return_20d < stock_filter.min_return_20d):
                continue
            if stock_filter.max_return_20d is not None and (return_20d is None or return_20d > stock_filter.max_return_20d):
                continue
            if stock_filter.min_operating_margin is not None:
                if latest_metric is None or latest_metric.operating_margin is None or latest_metric.operating_margin < stock_filter.min_operating_margin:
                    continue
            if stock_filter.min_roe is not None:
                if latest_metric is None or latest_metric.roe is None or latest_metric.roe < stock_filter.min_roe:
                    continue
            if stock_filter.require_recent_disclosure and not disclosures:
                continue

            reason_bits = [f"20d return {return_20d:.1f}%"]
            if latest_metric and latest_metric.operating_margin is not None:
                reason_bits.append(f"OP margin {latest_metric.operating_margin:.1f}%")
            if disclosures:
                reason_bits.append(f"{len(disclosures)} recent disclosures")

            candidates.append(
                ScreenCandidate(
                    ticker=profile.identifier.ticker,
                    name_ko=profile.identifier.name_ko,
                    market=profile.identifier.market,
                    close=latest.close,
                    return_20d=return_20d,
                    average_volume_20d=avg_volume,
                    operating_margin=latest_metric.operating_margin if latest_metric else None,
                    roe=latest_metric.roe if latest_metric else None,
                    disclosure_count_30d=len(disclosures),
                    reason=", ".join(reason_bits),
                )
            )

        return sorted(candidates, key=lambda item: (item.return_20d or 0), reverse=True)
