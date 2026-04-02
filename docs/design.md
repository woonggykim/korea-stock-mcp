# Design Notes

## Principles

- prefer official/public sources over scraping
- preserve source attribution and freshness metadata
- normalize identifiers across KRX, DART, and public data APIs
- support both screening and company-deep-dive workflows

## Planned production integrations

- KRX Open API for exchange-level market data and rankings
- Open DART for financial statements and disclosures
- data.go.kr for listed stock master data and lower-friction public endpoints

## Initial MCP tools

- `search_securities`
- `get_security_profile`
- `get_price_history`
- `get_financial_metrics`
- `get_recent_disclosures`
- `compare_stocks`
- `screen_stocks`
