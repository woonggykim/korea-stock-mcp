# Design Notes

## Principles

- prefer official/public sources over scraping
- preserve source attribution and freshness metadata
- normalize identifiers across KRX, DART, and public data APIs
- support both screening and company-deep-dive workflows

## Production integrations

- KRX Open API for exchange-level market data and rankings
- Open DART for financial statements and disclosures
- data.go.kr for listed stock master data and lower-friction public endpoints

Open DART and data.go.kr are wired in the initial implementation with mock fallback when credentials are missing.
KRX remains scaffolded because access is approval-driven and endpoint configuration depends on the granted API product.

## Initial MCP tools

- `search_securities`
- `get_security_profile`
- `get_price_history`
- `get_financial_metrics`
- `get_recent_disclosures`
- `compare_stocks`
- `screen_stocks`
- `summarize_investment_case`
- `get_market_snapshot`
