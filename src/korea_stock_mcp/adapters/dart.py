from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO
import zipfile
from xml.etree import ElementTree

import httpx

from korea_stock_mcp.adapters.base import MarketDataAdapter
from korea_stock_mcp.config import Settings
from korea_stock_mcp.mock_data import MOCK_DISCLOSURES, MOCK_METRICS, MOCK_SECURITIES
from korea_stock_mcp.models import DisclosureItem, FinancialMetric, PriceBar, SecurityProfile, SourceMeta


class OpenDartAdapter(MarketDataAdapter):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._corp_code_cache: dict[str, dict[str, str]] | None = None

    async def search_security(self, query: str) -> list[SecurityProfile]:
        if not self.settings.use_mock_data and self.settings.open_dart_api_key:
            matches = await self._search_security_live(query)
            if matches:
                return matches

        matches: list[SecurityProfile] = []
        for profile in MOCK_SECURITIES.values():
            if query.lower() in profile.identifier.name_ko.lower():
                matches.append(self._with_source(profile))
        return matches

    async def get_security_profile(self, ticker: str) -> SecurityProfile | None:
        if not self.settings.use_mock_data and self.settings.open_dart_api_key:
            profile = await self._get_security_profile_live(ticker)
            if profile:
                return profile

        profile = MOCK_SECURITIES.get(ticker)
        return self._with_source(profile) if profile else None

    async def get_price_history(self, ticker: str, limit: int = 60) -> list[PriceBar]:
        return []

    async def get_financial_metrics(self, ticker: str) -> list[FinancialMetric]:
        if not self.settings.use_mock_data and self.settings.open_dart_api_key:
            metrics = await self._get_financial_metrics_live(ticker)
            if metrics:
                return metrics
        return list(MOCK_METRICS.get(ticker, []))

    async def get_recent_disclosures(self, ticker: str, limit: int = 20) -> list[DisclosureItem]:
        if not self.settings.use_mock_data and self.settings.open_dart_api_key:
            disclosures = await self._get_recent_disclosures_live(ticker, limit)
            if disclosures:
                return disclosures
        return list(MOCK_DISCLOSURES.get(ticker, []))[:limit]

    def _with_source(self, profile: SecurityProfile) -> SecurityProfile:
        clone = profile.model_copy(deep=True)
        clone.source_meta.append(
            SourceMeta(source="open_dart", latency_class="filing_time", note="Mock Open DART adapter; replace with official API integration.")
        )
        return clone

    async def _search_security_live(self, query: str) -> list[SecurityProfile]:
        if not query:
            return []
        corp_codes = await self._load_corp_codes()
        if not corp_codes:
            return []

        lowered = query.lower()
        results: list[SecurityProfile] = []
        for item in corp_codes.values():
            if not query or lowered in item["corp_name"].lower() or lowered in item["stock_code"]:
                results.append(self._corp_code_entry_to_profile(item))
            if len(results) >= 20:
                break
        return results

    async def _get_security_profile_live(self, ticker: str) -> SecurityProfile | None:
        corp_code = await self._resolve_corp_code(ticker)
        if corp_code is None:
            return None

        payload = await self._get_json("company.json", {"corp_code": corp_code})
        if not payload or payload.get("status") != "000":
            return None

        corp_codes = await self._load_corp_codes()
        cache_entry = corp_codes.get(corp_code, {})
        market = self._map_corp_cls(payload.get("corp_cls"))
        return SecurityProfile(
            identifier={
                "ticker": payload.get("stock_code") or ticker,
                "name_ko": payload.get("corp_name") or cache_entry.get("corp_name") or ticker,
                "name_en": payload.get("corp_name_eng"),
                "market": market,
                "isin": cache_entry.get("isin"),
                "dart_corp_code": corp_code,
            },
            industry=payload.get("induty_code"),
            settlement_month=payload.get("acc_mt"),
            source_meta=[
                SourceMeta(
                    source="open_dart",
                    latency_class="filing_time",
                    note="Live company profile from Open DART.",
                )
            ],
        )

    async def _get_recent_disclosures_live(self, ticker: str, limit: int) -> list[DisclosureItem]:
        corp_code = await self._resolve_corp_code(ticker)
        if corp_code is None:
            return []

        today = date.today()
        start = today - timedelta(days=90)
        payload = await self._get_json(
            "list.json",
            {
                "corp_code": corp_code,
                "bgn_de": start.strftime("%Y%m%d"),
                "end_de": today.strftime("%Y%m%d"),
                "page_count": min(max(limit, 1), 100),
                "sort": "date",
                "sort_mth": "desc",
            },
        )
        if not payload or payload.get("status") != "000":
            return []

        items = payload.get("list", [])
        if isinstance(items, dict):
            items = [items]

        results: list[DisclosureItem] = []
        for item in items[:limit]:
            filed_at = item.get("rcept_dt", "")
            results.append(
                DisclosureItem(
                    receipt_no=item.get("rcept_no", ""),
                    filed_at=filed_at,
                    report_name=item.get("report_nm", ""),
                    corp_name=item.get("corp_name", ""),
                    market=self._map_corp_cls(item.get("corp_cls")),
                    category=item.get("flr_nm"),
                    url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item.get('rcept_no', '')}",
                )
            )
        return results

    async def _get_financial_metrics_live(self, ticker: str) -> list[FinancialMetric]:
        corp_code = await self._resolve_corp_code(ticker)
        if corp_code is None:
            return []

        results: list[FinancialMetric] = []
        today = date.today()
        years = [today.year, today.year - 1, today.year - 2]
        reports = [
            ("11011", "FY"),
            ("11014", "Q3"),
            ("11012", "H1"),
            ("11013", "Q1"),
        ]

        for year in years:
            for reprt_code, suffix in reports:
                payload = await self._get_json(
                    "fnlttSinglAcnt.json",
                    {
                        "corp_code": corp_code,
                        "bsns_year": str(year),
                        "reprt_code": reprt_code,
                    },
                )
                if not payload or payload.get("status") != "000":
                    continue

                accounts = payload.get("list", [])
                if isinstance(accounts, dict):
                    accounts = [accounts]
                metric = self._financial_metric_from_accounts(f"{year}-{suffix}", ticker, accounts)
                if metric:
                    results.append(metric)
                break

        return results

    async def _get_json(self, path: str, params: dict[str, str | int]) -> dict | None:
        if not self.settings.open_dart_api_key:
            return None

        request_params = {"crtfc_key": self.settings.open_dart_api_key, **params}
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(f"{self.settings.open_dart_api_base_url}/{path}", params=request_params)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError):
            return None

    async def _load_corp_codes(self) -> dict[str, dict[str, str]]:
        if self._corp_code_cache is not None:
            return self._corp_code_cache
        if not self.settings.open_dart_api_key:
            self._corp_code_cache = {}
            return self._corp_code_cache

        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(
                    f"{self.settings.open_dart_api_base_url}/corpCode.xml",
                    params={"crtfc_key": self.settings.open_dart_api_key},
                )
                response.raise_for_status()
        except httpx.HTTPError:
            self._corp_code_cache = {}
            return self._corp_code_cache

        records: dict[str, dict[str, str]] = {}
        try:
            with zipfile.ZipFile(BytesIO(response.content)) as archive:
                xml_name = archive.namelist()[0]
                xml_payload = archive.read(xml_name)
            root = ElementTree.fromstring(xml_payload)
        except (zipfile.BadZipFile, IndexError, ElementTree.ParseError):
            self._corp_code_cache = {}
            return self._corp_code_cache

        for entry in root.findall("list"):
            stock_code = (entry.findtext("stock_code") or "").strip()
            if not stock_code:
                continue
            corp_code = (entry.findtext("corp_code") or "").strip()
            records[corp_code] = {
                "corp_code": corp_code,
                "corp_name": (entry.findtext("corp_name") or "").strip(),
                "stock_code": stock_code,
                "modify_date": (entry.findtext("modify_date") or "").strip(),
            }

        self._corp_code_cache = records
        return records

    async def _resolve_corp_code(self, ticker: str) -> str | None:
        corp_codes = await self._load_corp_codes()
        for corp_code, item in corp_codes.items():
            if item.get("stock_code") == ticker:
                return corp_code
        mock_profile = MOCK_SECURITIES.get(ticker)
        if mock_profile:
            return mock_profile.identifier.dart_corp_code
        return None

    def _corp_code_entry_to_profile(self, item: dict[str, str]) -> SecurityProfile:
        return SecurityProfile(
            identifier={
                "ticker": item.get("stock_code", ""),
                "name_ko": item.get("corp_name", ""),
                "dart_corp_code": item.get("corp_code"),
            },
            source_meta=[
                SourceMeta(
                    source="open_dart",
                    latency_class="filing_time",
                    note="Resolved from Open DART corp code list.",
                )
            ],
        )

    def _financial_metric_from_accounts(
        self,
        period: str,
        ticker: str,
        accounts: list[dict],
    ) -> FinancialMetric | None:
        if not accounts:
            return None

        normalized = {self._normalize_account_name(item.get("account_nm", "")): item for item in accounts}
        revenue = self._account_amount(normalized, {"revenue", "sales", "매출액"})
        operating_income = self._account_amount(normalized, {"operatingincome", "영업이익"})
        net_income = self._account_amount(normalized, {"netincome", "당기순이익", "profitloss"})
        liabilities = self._account_amount(normalized, {"totalliabilities", "부채총계"})
        equity = self._account_amount(normalized, {"totalequity", "자본총계"})

        operating_margin = (operating_income / revenue * 100) if revenue and operating_income is not None else None
        roe = (net_income / equity * 100) if equity and net_income is not None else None
        debt_ratio = (liabilities / equity * 100) if equity and liabilities is not None else None

        shares = MOCK_SECURITIES.get(ticker).shares_outstanding if ticker in MOCK_SECURITIES else None
        eps = (net_income / shares) if shares and net_income is not None else None
        bps = (equity / shares) if shares and equity is not None else None

        return FinancialMetric(
            period=period,
            revenue=revenue,
            operating_income=operating_income,
            net_income=net_income,
            operating_margin=operating_margin,
            roe=roe,
            debt_ratio=debt_ratio,
            eps=eps,
            bps=bps,
        )

    def _account_amount(self, accounts: dict[str, dict], candidates: set[str]) -> int | None:
        for candidate in candidates:
            key = self._normalize_account_name(candidate)
            item = accounts.get(key)
            if item:
                raw_value = item.get("thstrm_amount") or item.get("frmtrm_amount") or item.get("bfefrmtrm_amount")
                if raw_value is None:
                    continue
                try:
                    return int(str(raw_value).replace(",", ""))
                except ValueError:
                    continue
        return None

    def _normalize_account_name(self, value: str) -> str:
        return "".join(ch.lower() for ch in value if ch.isalnum() or "\uac00" <= ch <= "\ud7a3")

    def _map_corp_cls(self, corp_cls: str | None) -> str | None:
        return {
            "Y": "KOSPI",
            "K": "KOSDAQ",
            "N": "KONEX",
            "E": "OTHER",
        }.get(corp_cls or "")
