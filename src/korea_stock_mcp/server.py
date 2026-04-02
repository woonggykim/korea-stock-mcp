from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from korea_stock_mcp.config import load_settings
from korea_stock_mcp.models import ScreenFilter
from korea_stock_mcp.services import KoreaStockService


def build_server() -> FastMCP:
    settings = load_settings()
    service = KoreaStockService(settings)
    mcp = FastMCP(name="korea-stock-mcp")

    @mcp.tool()
    async def search_securities(query: str) -> dict:
        results = await service.search_securities(query)
        return {"query": query, "results": [item.model_dump() for item in results]}

    @mcp.tool()
    async def get_security_profile(ticker: str) -> dict:
        profile = await service.get_security_profile(ticker)
        return {"ticker": ticker, "profile": profile.model_dump() if profile else None}

    @mcp.tool()
    async def get_price_history(ticker: str, limit: int = 60) -> dict:
        history = await service.get_price_history(ticker, limit)
        return {"ticker": ticker, "history": [bar.model_dump() for bar in history]}

    @mcp.tool()
    async def get_market_snapshot(market: str = "KOSPI") -> dict:
        snapshot = await service.get_market_snapshot(market)
        return {"market": market, "snapshot": snapshot.model_dump() if snapshot else None}

    @mcp.tool()
    async def get_financial_metrics(ticker: str) -> dict:
        metrics = await service.get_financial_metrics(ticker)
        return {"ticker": ticker, "metrics": [metric.model_dump() for metric in metrics]}

    @mcp.tool()
    async def get_recent_disclosures(ticker: str, limit: int = 20) -> dict:
        disclosures = await service.get_recent_disclosures(ticker, limit)
        return {"ticker": ticker, "disclosures": [item.model_dump() for item in disclosures]}

    @mcp.tool()
    async def compare_stocks(tickers: list[str]) -> dict:
        comparison = await service.compare_stocks(tickers)
        return comparison.model_dump()

    @mcp.tool()
    async def summarize_investment_case(ticker: str) -> dict:
        summary = await service.summarize_investment_case(ticker)
        return {"ticker": ticker, "summary": summary.model_dump() if summary else None}

    @mcp.tool()
    async def screen_stocks(
        market: str | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        min_volume: int | None = None,
        min_return_20d: float | None = None,
        max_return_20d: float | None = None,
        min_operating_margin: float | None = None,
        min_roe: float | None = None,
        require_recent_disclosure: bool = False,
    ) -> dict:
        stock_filter = ScreenFilter(
            market=market,
            min_price=min_price,
            max_price=max_price,
            min_volume=min_volume,
            min_return_20d=min_return_20d,
            max_return_20d=max_return_20d,
            min_operating_margin=min_operating_margin,
            min_roe=min_roe,
            require_recent_disclosure=require_recent_disclosure,
        )
        matches = await service.screen_stocks(stock_filter)
        return {"filter": stock_filter.model_dump(), "results": [item.model_dump() for item in matches]}

    return mcp
