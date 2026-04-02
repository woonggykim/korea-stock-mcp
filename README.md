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
- mock mode for local development without credentials

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m korea_stock_mcp
```
