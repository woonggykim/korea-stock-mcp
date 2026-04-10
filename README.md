# korea-stock-mcp

MCP server for Korean stock research using official and public sources:

- KRX Open API
- Open DART
- data.go.kr

## Status

Initial implementation includes:

- source adapters and typed models
- identifier resolution and data normalization
- MCP tools for profile, price history, disclosures, financial metrics, comparison, and screening
- live integrations for Open DART and data.go.kr with mock fallback for local development
- a KRX adapter scaffold for future approved endpoint wiring

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m korea_stock_mcp
```

## Environment

Set the credentials you have available:

```bash
export OPEN_DART_API_KEY=...
export PUBLIC_DATA_API_KEY=...
export PUBLIC_DATA_FINANCIAL_API_BASE_URL=https://apis.data.go.kr/1160100/service/GetFinaStatInfoService_V2
export KOREA_STOCK_MCP_USE_MOCK_DATA=0
```

Live data is the default. Set `KOREA_STOCK_MCP_USE_MOCK_DATA=1` when you want deterministic local responses without network access.
