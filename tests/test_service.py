from __future__ import annotations

import asyncio
import unittest

from korea_stock_mcp.config import Settings
from korea_stock_mcp.services import KoreaStockService


class KoreaStockServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = KoreaStockService(Settings(use_mock_data=True))

    def test_get_security_profile(self) -> None:
        profile = asyncio.run(self.service.get_security_profile("005930"))
        self.assertIsNotNone(profile)
        self.assertEqual(profile.identifier.name_ko, "삼성전자")
        self.assertTrue(profile.source_meta)

    def test_compare_stocks(self) -> None:
        comparison = asyncio.run(self.service.compare_stocks(["005930", "000660"]))
        self.assertEqual(len(comparison.profiles), 2)
        self.assertIn("005930", comparison.latest_metrics)

    def test_screen_stocks(self) -> None:
        results = asyncio.run(
            self.service.screen_stocks(
                stock_filter={
                    "market": "KOSPI",
                    "min_operating_margin": 10.0,
                }
            )
        )
        self.assertTrue(results)


if __name__ == "__main__":
    unittest.main()
