from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


LatencyClass = Literal["realtime_like", "end_of_day", "next_business_day", "filing_time", "unknown"]


class SourceMeta(BaseModel):
    source: str
    as_of: str | None = None
    latency_class: LatencyClass = "unknown"
    note: str | None = None


class SecurityIdentifier(BaseModel):
    ticker: str
    name_ko: str
    name_en: str | None = None
    market: str | None = None
    isin: str | None = None
    dart_corp_code: str | None = None


class SecurityProfile(BaseModel):
    identifier: SecurityIdentifier
    sector: str | None = None
    industry: str | None = None
    listing_date: str | None = None
    shares_outstanding: int | None = None
    par_value: int | None = None
    settlement_month: str | None = None
    source_meta: list[SourceMeta] = Field(default_factory=list)


class PriceBar(BaseModel):
    date: str
    open: int | None = None
    high: int | None = None
    low: int | None = None
    close: int
    volume: int | None = None
    turnover: int | None = None


class FinancialMetric(BaseModel):
    period: str
    revenue: int | None = None
    operating_income: int | None = None
    net_income: int | None = None
    operating_margin: float | None = None
    roe: float | None = None
    debt_ratio: float | None = None
    eps: float | None = None
    bps: float | None = None


class DisclosureItem(BaseModel):
    receipt_no: str
    filed_at: str
    report_name: str
    corp_name: str
    market: str | None = None
    category: str | None = None
    url: str | None = None


class StockComparison(BaseModel):
    profiles: list[SecurityProfile]
    latest_prices: dict[str, PriceBar]
    latest_metrics: dict[str, FinancialMetric]
    recent_disclosures: dict[str, list[DisclosureItem]]


class MarketSnapshot(BaseModel):
    market: str
    advancers: int
    decliners: int
    unchanged: int
    total_volume: int
    total_turnover: int
    top_movers: list[str] = Field(default_factory=list)


class InvestmentSummary(BaseModel):
    ticker: str
    company_name: str
    market_view: str
    financial_view: str
    disclosure_view: str
    risks: list[str]
    source_notes: list[str]


class ScreenFilter(BaseModel):
    market: str | None = None
    min_price: int | None = None
    max_price: int | None = None
    min_volume: int | None = None
    min_return_20d: float | None = None
    max_return_20d: float | None = None
    min_operating_margin: float | None = None
    min_roe: float | None = None
    require_recent_disclosure: bool = False


class ScreenCandidate(BaseModel):
    ticker: str
    name_ko: str
    market: str | None = None
    close: int | None = None
    return_20d: float | None = None
    average_volume_20d: float | None = None
    operating_margin: float | None = None
    roe: float | None = None
    disclosure_count_30d: int = 0
    reason: str
