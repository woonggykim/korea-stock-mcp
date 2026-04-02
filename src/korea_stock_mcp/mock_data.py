from __future__ import annotations

from korea_stock_mcp.models import (
    DisclosureItem,
    FinancialMetric,
    MarketSnapshot,
    PriceBar,
    SecurityIdentifier,
    SecurityProfile,
)


MOCK_SECURITIES = {
    "005930": SecurityProfile(
        identifier=SecurityIdentifier(
            ticker="005930",
            name_ko="삼성전자",
            name_en="Samsung Electronics",
            market="KOSPI",
            isin="KR7005930003",
            dart_corp_code="00126380",
        ),
        sector="전기전자",
        industry="반도체",
        listing_date="1975-06-11",
        shares_outstanding=5969782550,
        par_value=100,
        settlement_month="12",
        source_meta=[],
    ),
    "000660": SecurityProfile(
        identifier=SecurityIdentifier(
            ticker="000660",
            name_ko="SK하이닉스",
            name_en="SK hynix",
            market="KOSPI",
            isin="KR7000660001",
            dart_corp_code="00164779",
        ),
        sector="전기전자",
        industry="반도체",
        listing_date="1996-12-26",
        shares_outstanding=728002365,
        par_value=5000,
        settlement_month="12",
        source_meta=[],
    ),
}

MOCK_PRICES = {
    "005930": [
        PriceBar(date="2026-03-05", close=73000, volume=12100000, open=72500, high=73300, low=72100),
        PriceBar(date="2026-03-12", close=74200, volume=11800000, open=73400, high=74400, low=73100),
        PriceBar(date="2026-03-19", close=75100, volume=13300000, open=74400, high=75200, low=74000),
        PriceBar(date="2026-03-26", close=76300, volume=14100000, open=75500, high=76500, low=75300),
        PriceBar(date="2026-04-01", close=77100, volume=15200000, open=76800, high=77300, low=76400),
    ],
    "000660": [
        PriceBar(date="2026-03-05", close=192000, volume=3050000, open=189500, high=193000, low=188000),
        PriceBar(date="2026-03-12", close=198500, volume=3320000, open=194000, high=199500, low=193500),
        PriceBar(date="2026-03-19", close=204000, volume=3540000, open=199000, high=205500, low=198500),
        PriceBar(date="2026-03-26", close=211000, volume=3620000, open=206500, high=212500, low=205500),
        PriceBar(date="2026-04-01", close=216000, volume=3770000, open=212500, high=217000, low=211500),
    ],
}

MOCK_METRICS = {
    "005930": [
        FinancialMetric(period="2025-Q4", revenue=76400000000000, operating_income=8900000000000, net_income=7600000000000, operating_margin=11.6, roe=9.8, debt_ratio=27.2, eps=1245.0, bps=52000.0),
    ],
    "000660": [
        FinancialMetric(period="2025-Q4", revenue=18200000000000, operating_income=4200000000000, net_income=3500000000000, operating_margin=23.1, roe=16.4, debt_ratio=31.5, eps=4810.0, bps=104000.0),
    ],
}

MOCK_DISCLOSURES = {
    "005930": [
        DisclosureItem(
            receipt_no="20260318000123",
            filed_at="2026-03-18T16:22:00+09:00",
            report_name="사업보고서",
            corp_name="삼성전자",
            market="KOSPI",
            category="정기공시",
            url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260318000123",
        )
    ],
    "000660": [
        DisclosureItem(
            receipt_no="20260325000456",
            filed_at="2026-03-25T17:01:00+09:00",
            report_name="주요사항보고서(시설투자)",
            corp_name="SK하이닉스",
            market="KOSPI",
            category="주요사항",
            url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260325000456",
        )
    ],
}

MOCK_MARKET_SNAPSHOTS = {
    "KOSPI": MarketSnapshot(
        market="KOSPI",
        advancers=421,
        decliners=379,
        unchanged=73,
        total_volume=682000000,
        total_turnover=12700000000000,
        top_movers=["000660", "005930"],
    ),
    "KOSDAQ": MarketSnapshot(
        market="KOSDAQ",
        advancers=712,
        decliners=621,
        unchanged=114,
        total_volume=1034000000,
        total_turnover=8900000000000,
        top_movers=["091990", "196170"],
    ),
}
