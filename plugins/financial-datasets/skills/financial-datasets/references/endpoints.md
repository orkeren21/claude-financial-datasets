# Financial Datasets API — endpoint reference

Base URL: `https://api.financialdatasets.ai` · Auth header: `X-API-KEY` · 49 endpoints

All calls go through `scripts/fds.py`. For a GET, every parameter below is a `--flag value`. For the two POST endpoints, pass the body with `--json '{...}'`.

## Contents

- [Company Information](#company-information) (3)
- [Earnings](#earnings) (2)
- [Financial Metrics](#financial-metrics) (3)
- [Financial Statements](#financial-statements) (15)
- [Index Funds](#index-funds) (2)
- [Insider Trades](#insider-trades) (1)
- [Institutional Holdings](#institutional-holdings) (3)
- [KPIs](#kpis) (5)
- [Macroeconomics](#macroeconomics) (3)
- [Market Data](#market-data) (5)
- [News](#news) (1)
- [SEC Filings](#sec-filings) (6)


## Company Information

### `GET /company/facts`
Get company facts. Get company facts for a ticker.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The ticker symbol. |
| `cik` |  | string | The CIK of the company. |

Example: `python fds.py /company/facts `

### `GET /company/facts/ciks`
Available CIKs for company facts. Returns a list of available CIKs for the company facts endpoint. This endpoint is free and does not require authentication.

Example: `python fds.py /company/facts/ciks `

### `GET /company/facts/tickers`
Available tickers for company facts. Returns a list of available tickers for the company facts endpoint. This endpoint is free and does not require authentication.

Example: `python fds.py /company/facts/tickers `


## Earnings

### `GET /earnings`
Get earnings snapshot. Get the most recent earnings snapshot for a ticker. Optional estimate/surprise and change fields are returned only when available.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` | yes | string | The ticker symbol (e.g. `AAPL`). |
| `limit` |  | integer | Number of most-recent **report periods** worth of filings to return, sorted by `(report_period DESC, filing_date ASC)`. The number of entries returned may exceed `limit` when a recent period has both an 8-K and a 10-Q / 10-K. Values above 40 are clamped to 40. Non-positive or non-integer values return 400. |

Example: `python fds.py /earnings --ticker <ticker>`

### `GET /earnings/tickers`
Available tickers for earnings. Returns a list of available tickers for the earnings endpoint. This endpoint is free and does not require authentication.

Example: `python fds.py /earnings/tickers `


## Financial Metrics

### `GET /financial-metrics`
Get financial metrics. Get financial metrics for a ticker, including valuation, profitability, efficiency, liquidity, leverage, growth, and per share metrics.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The ticker symbol of the company. Required if cik is not provided. |
| `cik` |  | string | The Central Index Key (CIK) of the company. Can be used instead of ticker. |
| `period` | yes | annual \| quarterly \| ttm | The time period for the financial data. |
| `limit` |  | integer | The maximum number of results to return. |
| `report_period` |  | string | Filter by exact report period date in YYYY-MM-DD format. |
| `report_period_gte` |  | string | Filter by report period greater than or equal to date in YYYY-MM-DD format. |
| `report_period_lte` |  | string | Filter by report period less than or equal to date in YYYY-MM-DD format. |
| `report_period_gt` |  | string | Filter by report period greater than date in YYYY-MM-DD format. |
| `report_period_lt` |  | string | Filter by report period less than date in YYYY-MM-DD format. |

Example: `python fds.py /financial-metrics --period <period>`

### `GET /financial-metrics/snapshot`
Financial Metrics Snapshot (Real-Time). Get the real-time financial metrics snapshot for a stock, including valuation ratios, profitability, efficiency, liquidity, leverage, growth, and per share metrics.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The ticker symbol of the company. |
| `cik` |  | string | The Central Index Key (CIK) of the company. Can be used instead of ticker. |

Example: `python fds.py /financial-metrics/snapshot `

### `GET /financial-metrics/snapshot/tickers`
Available tickers for financial metrics snapshots. Returns a list of available tickers for the financial metrics snapshot endpoint. This endpoint is free and does not require authentication.

Example: `python fds.py /financial-metrics/snapshot/tickers `


## Financial Statements

### `GET /financials`
Get all financial statements. Get all financial statements for a ticker.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The ticker symbol. Required if cik is not provided. |
| `period` | yes | annual \| quarterly \| ttm | The time period of the financial statements. |
| `limit` |  | integer | The maximum number of financial statements to return. |
| `cik` |  | string | The Central Index Key (CIK) of the company. |
| `report_period` |  | string | Filter by exact report period date in YYYY-MM-DD format. |
| `report_period_gte` |  | string | Filter by report period greater than or equal to date in YYYY-MM-DD format. |
| `report_period_lte` |  | string | Filter by report period less than or equal to date in YYYY-MM-DD format. |
| `report_period_gt` |  | string | Filter by report period greater than date in YYYY-MM-DD format. |
| `report_period_lt` |  | string | Filter by report period less than date in YYYY-MM-DD format. |

Example: `python fds.py /financials --period <period>`

### `GET /financials/as-reported`
Get all as-reported financials. Get the as-filed hierarchies for income statement, balance sheet, and cash flow statement in a single API call. Each period contains three nested objects; any one may be null if data is missing.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The ticker symbol. Required if cik is not provided. |
| `period` | yes | annual \| quarterly | The time period of the data. |
| `limit` |  | integer | The maximum number of periods to return. |
| `cik` |  | string | The Central Index Key (CIK) of the company. |
| `report_period` |  | string | Filter by exact report period date in YYYY-MM-DD format. |
| `report_period_gte` |  | string | Filter by report period greater than or equal to date in YYYY-MM-DD format. |
| `report_period_lte` |  | string | Filter by report period less than or equal to date in YYYY-MM-DD format. |
| `report_period_gt` |  | string | Filter by report period greater than date in YYYY-MM-DD format. |
| `report_period_lt` |  | string | Filter by report period less than date in YYYY-MM-DD format. |

Example: `python fds.py /financials/as-reported --period <period>`

### `GET /financials/balance-sheets`
Get balance sheets. Get balance sheets for a ticker.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The ticker symbol. Required if cik is not provided. |
| `period` | yes | annual \| quarterly \| ttm | The time period of the balance sheets. |
| `limit` |  | integer | The maximum number of balance sheets to return |
| `cik` |  | string | The Central Index Key (CIK) of the company. |
| `report_period` |  | string | Filter by exact report period date in YYYY-MM-DD format. |
| `report_period_gte` |  | string | Filter by report period greater than or equal to date in YYYY-MM-DD format. |
| `report_period_lte` |  | string | Filter by report period less than or equal to date in YYYY-MM-DD format. |
| `report_period_gt` |  | string | Filter by report period greater than date in YYYY-MM-DD format. |
| `report_period_lt` |  | string | Filter by report period less than date in YYYY-MM-DD format. |

Example: `python fds.py /financials/balance-sheets --period <period>`

### `GET /financials/balance-sheets/as-reported`
Get balance sheet (as-reported). Get the as-filed balance sheet hierarchy. Each line item is returned exactly as it appears on the face of the 10-K or 10-Q, with parent-child relationships preserved in the `children` field.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The ticker symbol. Required if cik is not provided. |
| `period` | yes | annual \| quarterly | The time period of the data. |
| `limit` |  | integer | The maximum number of periods to return. |
| `cik` |  | string | The Central Index Key (CIK) of the company. |
| `report_period` |  | string | Filter by exact report period date in YYYY-MM-DD format. |
| `report_period_gte` |  | string | Filter by report period greater than or equal to date in YYYY-MM-DD format. |
| `report_period_lte` |  | string | Filter by report period less than or equal to date in YYYY-MM-DD format. |
| `report_period_gt` |  | string | Filter by report period greater than date in YYYY-MM-DD format. |
| `report_period_lt` |  | string | Filter by report period less than date in YYYY-MM-DD format. |

Example: `python fds.py /financials/balance-sheets/as-reported --period <period>`

### `GET /financials/balance-sheets/segments`
Get balance sheet segments. Get balance sheet segment breakdowns (assets, goodwill, long-lived assets) by business segment.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The ticker symbol. Required if cik is not provided. |
| `period` | yes | annual \| quarterly | The time period of the data. |
| `limit` |  | integer | The maximum number of periods to return. |
| `cik` |  | string | The Central Index Key (CIK) of the company. |
| `report_period` |  | string | Filter by exact report period date in YYYY-MM-DD format. |
| `report_period_gte` |  | string | Filter by report period greater than or equal to date in YYYY-MM-DD format. |
| `report_period_lte` |  | string | Filter by report period less than or equal to date in YYYY-MM-DD format. |
| `report_period_gt` |  | string | Filter by report period greater than date in YYYY-MM-DD format. |
| `report_period_lt` |  | string | Filter by report period less than date in YYYY-MM-DD format. |

Example: `python fds.py /financials/balance-sheets/segments --period <period>`

### `GET /financials/cash-flow-statements`
Get cash flow statements. Get cash flow statements for a ticker.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The ticker symbol. Required if cik is not provided. |
| `period` | yes | annual \| quarterly \| ttm | The time period of the cash flow statements. |
| `limit` |  | integer | The maximum number of cash flow statements to return. |
| `cik` |  | string | The Central Index Key (CIK) of the company. |
| `report_period` |  | string | Filter by exact report period date in YYYY-MM-DD format. |
| `report_period_gte` |  | string | Filter by report period greater than or equal to date in YYYY-MM-DD format. |
| `report_period_lte` |  | string | Filter by report period less than or equal to date in YYYY-MM-DD format. |
| `report_period_gt` |  | string | Filter by report period greater than date in YYYY-MM-DD format. |
| `report_period_lt` |  | string | Filter by report period less than date in YYYY-MM-DD format. |

Example: `python fds.py /financials/cash-flow-statements --period <period>`

### `GET /financials/cash-flow-statements/as-reported`
Get cash flow statement (as-reported). Get the as-filed cash flow statement hierarchy. Each line item is returned exactly as it appears on the face of the 10-K or 10-Q, with parent-child relationships preserved in the `children` field.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The ticker symbol. Required if cik is not provided. |
| `period` | yes | annual \| quarterly | The time period of the data. |
| `limit` |  | integer | The maximum number of periods to return. |
| `cik` |  | string | The Central Index Key (CIK) of the company. |
| `report_period` |  | string | Filter by exact report period date in YYYY-MM-DD format. |
| `report_period_gte` |  | string | Filter by report period greater than or equal to date in YYYY-MM-DD format. |
| `report_period_lte` |  | string | Filter by report period less than or equal to date in YYYY-MM-DD format. |
| `report_period_gt` |  | string | Filter by report period greater than date in YYYY-MM-DD format. |
| `report_period_lt` |  | string | Filter by report period less than date in YYYY-MM-DD format. |

Example: `python fds.py /financials/cash-flow-statements/as-reported --period <period>`

### `GET /financials/cash-flow-statements/segments`
Get cash flow statement segments. Get cash flow statement segment breakdowns (capital expenditure) by business segment.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The ticker symbol. Required if cik is not provided. |
| `period` | yes | annual \| quarterly | The time period of the data. |
| `limit` |  | integer | The maximum number of periods to return. |
| `cik` |  | string | The Central Index Key (CIK) of the company. |
| `report_period` |  | string | Filter by exact report period date in YYYY-MM-DD format. |
| `report_period_gte` |  | string | Filter by report period greater than or equal to date in YYYY-MM-DD format. |
| `report_period_lte` |  | string | Filter by report period less than or equal to date in YYYY-MM-DD format. |
| `report_period_gt` |  | string | Filter by report period greater than date in YYYY-MM-DD format. |
| `report_period_lt` |  | string | Filter by report period less than date in YYYY-MM-DD format. |

Example: `python fds.py /financials/cash-flow-statements/segments --period <period>`

### `GET /financials/income-statements`
Get income statements. Get income statements for a ticker.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The ticker symbol. Required if cik is not provided. |
| `period` | yes | annual \| quarterly \| ttm | The time period of the income statements. |
| `limit` |  | integer | The maximum number of income statements to return. |
| `cik` |  | string | The Central Index Key (CIK) of the company. |
| `report_period` |  | string | Filter by exact report period date in YYYY-MM-DD format. |
| `report_period_gte` |  | string | Filter by report period greater than or equal to date in YYYY-MM-DD format. |
| `report_period_lte` |  | string | Filter by report period less than or equal to date in YYYY-MM-DD format. |
| `report_period_gt` |  | string | Filter by report period greater than date in YYYY-MM-DD format. |
| `report_period_lt` |  | string | Filter by report period less than date in YYYY-MM-DD format. |

Example: `python fds.py /financials/income-statements --period <period>`

### `GET /financials/income-statements/as-reported`
Get income statement (as-reported). Get the as-filed income statement hierarchy. Each line item is returned exactly as it appears on the face of the 10-K or 10-Q, with parent-child relationships preserved in the `children` field.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The ticker symbol. Required if cik is not provided. |
| `period` | yes | annual \| quarterly | The time period of the data. |
| `limit` |  | integer | The maximum number of periods to return. |
| `cik` |  | string | The Central Index Key (CIK) of the company. |
| `report_period` |  | string | Filter by exact report period date in YYYY-MM-DD format. |
| `report_period_gte` |  | string | Filter by report period greater than or equal to date in YYYY-MM-DD format. |
| `report_period_lte` |  | string | Filter by report period less than or equal to date in YYYY-MM-DD format. |
| `report_period_gt` |  | string | Filter by report period greater than date in YYYY-MM-DD format. |
| `report_period_lt` |  | string | Filter by report period less than date in YYYY-MM-DD format. |

Example: `python fds.py /financials/income-statements/as-reported --period <period>`

### `GET /financials/income-statements/segments`
Get income statement segments. Get income statement segment breakdowns (revenue, operating income, depreciation) by product and business segment.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The ticker symbol. Required if cik is not provided. |
| `period` | yes | annual \| quarterly | The time period of the data. |
| `limit` |  | integer | The maximum number of periods to return. |
| `cik` |  | string | The Central Index Key (CIK) of the company. |
| `report_period` |  | string | Filter by exact report period date in YYYY-MM-DD format. |
| `report_period_gte` |  | string | Filter by report period greater than or equal to date in YYYY-MM-DD format. |
| `report_period_lte` |  | string | Filter by report period less than or equal to date in YYYY-MM-DD format. |
| `report_period_gt` |  | string | Filter by report period greater than date in YYYY-MM-DD format. |
| `report_period_lt` |  | string | Filter by report period less than date in YYYY-MM-DD format. |

Example: `python fds.py /financials/income-statements/segments --period <period>`

### `POST /financials/search/line-items`
Search specific financial metrics. Search for specific financial metrics across income statements, balance sheets, and cash flow statements for a list of tickers.

_JSON body fields:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `line_items` | yes | array | An array of line items to apply to the search. |
| `tickers` | yes | array | An array of tickers to apply to the search. |
| `period` |  | annual \| quarterly \| ttm | The time period for the financial data. |
| `limit` |  | integer | The maximum number of results to return. |

Example: `python fds.py /financials/search/line-items --json '{...}'`

### `POST /financials/search/screener`
Search financial statements. Search for stocks by filtering across financial metrics from income statements, balance sheets, and cash flow statements.

_JSON body fields:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `limit` |  | integer | The maximum number of results to return. |
| `filters` | yes | array | An array of filter objects to apply to the search. |

Example: `python fds.py /financials/search/screener --json '{...}'`

### `GET /financials/search/screener/filters`
Available screener filter fields. Returns a list of available filter fields, valid values, and operators for the stock screener endpoint. This endpoint is free and does not require authentication.

Example: `python fds.py /financials/search/screener/filters `

### `GET /financials/segments`
Get all segmented financials. Get segment breakdowns from all three financial statement types (income statement, balance sheet, cash flow) in a single API call.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The ticker symbol. Required if cik is not provided. |
| `period` | yes | annual \| quarterly | The time period of the data. |
| `limit` |  | integer | The maximum number of periods to return. |
| `cik` |  | string | The Central Index Key (CIK) of the company. |
| `report_period` |  | string | Filter by exact report period date in YYYY-MM-DD format. |
| `report_period_gte` |  | string | Filter by report period greater than or equal to date in YYYY-MM-DD format. |
| `report_period_lte` |  | string | Filter by report period less than or equal to date in YYYY-MM-DD format. |
| `report_period_gt` |  | string | Filter by report period greater than date in YYYY-MM-DD format. |
| `report_period_lt` |  | string | Filter by report period less than date in YYYY-MM-DD format. |

Example: `python fds.py /financials/segments --period <period>`


## Index Funds

### `GET /index-funds`
Get ETF / index-fund holdings. Query fund holdings in two directions. Provide exactly one of `ticker` or `holding`. `?ticker=SPY` returns a fund's constituents and each position's weight (the fund's latest filing by default, or the composition in effect on/before `as_of`). `?holding=AAPL` returns the funds whose latest filing holds that security, sorted by weight.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The fund's ticker symbol (e.g., `SPY`). Returns that fund's holdings. Mutually exclusive with `holding`. |
| `holding` |  | string | A held security's ticker symbol (e.g., `AAPL`). Returns the funds whose latest filing holds it. Mutually exclusive with `ticker`. |
| `as_of` |  | string | Only valid with `ticker`. Returns the fund composition in effect on or before this date (YYYY-MM-DD). Without it, the fund's latest filing is returned. |
| `asset_class` |  | equity \| bond | Only valid with `ticker`. Filter constituents by instrument type: `equity` or `bond`. Omit for all holdings. |
| `limit` |  | integer | The maximum number of rows to return (default: 50, max: 1000). |
| `offset` |  | integer | The number of rows to skip, for pagination (default: 0). |

Example: `python fds.py /index-funds `

### `GET /index-funds/tickers`
List available fund tickers (discovery). Returns the list of fund ticker symbols available in the API. No API key required.

Example: `python fds.py /index-funds/tickers `


## Insider Trades

### `GET /insider-trades`
Get insider trades. Get insider trades like buys and sells for a ticker by a company insider.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` | yes | string | The ticker symbol of the company. |
| `limit` |  | integer | The maximum number of transactions to return (default: 10). |
| `name` |  | string | Filter by insider name (e.g., 'Jen Hsun Huang'). Use the /insider-trades/names endpoint to get available names for a ticker. |
| `transaction_type` |  | string | Filter by transaction type (e.g., 'Open market sale', 'Gift'). Use the /insider-trades/transaction-types endpoint to get available types. |
| `filing_date` |  | string | Filter by exact filing date in YYYY-MM-DD format. |
| `filing_date_gte` |  | string | Filter by filing date greater than or equal to this date (YYYY-MM-DD). |
| `filing_date_lte` |  | string | Filter by filing date less than or equal to this date (YYYY-MM-DD). |
| `filing_date_gt` |  | string | Filter by filing date greater than this date (YYYY-MM-DD). |
| `filing_date_lt` |  | string | Filter by filing date less than this date (YYYY-MM-DD). |

Example: `python fds.py /insider-trades --ticker <ticker>`


## Institutional Holdings

### `GET /institutional-holdings`
Get 13F institutional holdings. Query 13F institutional holdings by filer CIK or by held ticker. Provide exactly one of `filer_cik` or `ticker`. When no `report_period` filter is supplied, `?filer_cik=...` returns the filer's most recent 13F and `?ticker=...` returns one position per institutional filer whose most recent 13F currently includes the ticker (filers who have since dropped the position are excluded).

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `filer_cik` |  | string | The 10-digit zero-padded SEC CIK of the institutional filer. Mutually exclusive with `ticker`. |
| `ticker` |  | string | The held security's ticker symbol. Mutually exclusive with `filer_cik`. Without a `report_period` filter, returns one position per institutional filer whose most recent 13F currently includes this ticker. |
| `limit` |  | integer | The maximum number of positions to return (default: 10, max: 200). |
| `report_period` |  | string | Filter by exact report period date in YYYY-MM-DD format. |
| `report_period_gte` |  | string | Filter by report period greater than or equal to date in YYYY-MM-DD format. |
| `report_period_lte` |  | string | Filter by report period less than or equal to date in YYYY-MM-DD format. |
| `report_period_gt` |  | string | Filter by report period greater than date in YYYY-MM-DD format. |
| `report_period_lt` |  | string | Filter by report period less than date in YYYY-MM-DD format. |

Example: `python fds.py /institutional-holdings `

### `GET /institutional-holdings/investors`
Find an investor's CIK by name (discovery). Returns up to 100 distinct institutional filers (CIK + name). Use the optional `name` parameter for case-insensitive prefix search. No API key required.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `name` |  | string | Optional case-insensitive prefix to filter filer names (e.g., `BERK`). |

Example: `python fds.py /institutional-holdings/investors `

### `GET /institutional-holdings/tickers`
List tickers currently held by any 13F filer (discovery). Returns the list of ticker symbols that appear as held securities across 13F filings. No API key required.

Example: `python fds.py /institutional-holdings/tickers `


## KPIs

### `GET /kpi/guidance`
Get forward guidance. Get structured forward guidance from earnings releases. Returns ranges, point estimates, and directional signals.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` | yes | string | The ticker symbol. |
| `metric_name` |  | string | Filter to a specific metric. |
| `period` |  | quarterly \| annual | Filter by period type: quarterly or annual. |
| `report_period_gte` |  | string | Only return guidance on or after this date (YYYY-MM-DD). |
| `report_period_lte` |  | string | Only return guidance on or before this date (YYYY-MM-DD). |
| `limit` |  | integer | Number of periods to return. |

Example: `python fds.py /kpi/guidance --ticker <ticker>`

### `GET /kpi/metrics`
Get KPI metrics. Get sector-specific operational KPIs for a ticker. Includes metrics like load factor, CET1 ratio, same-store sales, FFO per share, and more. Sourced from SEC 8-K earnings releases.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` | yes | string | The ticker symbol. |
| `metric_name` |  | string | Filter to a specific metric (e.g., load_factor, cet1_ratio). |
| `period` |  | quarterly \| annual | Filter by period type: quarterly or annual. |
| `report_period_gte` |  | string | Only return metrics on or after this date (YYYY-MM-DD). |
| `report_period_lte` |  | string | Only return metrics on or before this date (YYYY-MM-DD). |
| `limit` |  | integer | Number of periods to return. Returns all metrics for the N most recent periods. |

Example: `python fds.py /kpi/metrics --ticker <ticker>`

### `GET /kpi/metrics/sectors`
Get available KPI sectors. Returns a list of sectors that have KPI metrics available.

Example: `python fds.py /kpi/metrics/sectors `

### `GET /kpi/metrics/tickers`
Get available KPI tickers. Returns a list of tickers that have KPI metrics available.

Example: `python fds.py /kpi/metrics/tickers `

### `GET /kpi/non-gaap`
Get non-GAAP metrics. Get non-GAAP financial metrics with GAAP equivalents and key adjustments.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` | yes | string | The ticker symbol. |
| `metric_name` |  | string | Filter to a specific metric. |
| `period` |  | quarterly \| annual | Filter by period type: quarterly or annual. |
| `report_period_gte` |  | string | Only return metrics on or after this date (YYYY-MM-DD). |
| `report_period_lte` |  | string | Only return metrics on or before this date (YYYY-MM-DD). |
| `limit` |  | integer | Number of periods to return. |

Example: `python fds.py /kpi/non-gaap --ticker <ticker>`


## Macroeconomics

### `GET /macro/interest-rates`
Interest Rates (Historical). Historical interest rates for all major central banks in the world.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `bank` | yes | string | The bank whose interest rates to return. Use the /macro/interest-rates/banks endpoint to get a list of available banks. |
| `start_date` |  | string | The start date of the interest rates to return in YYYY-MM-DD format. |
| `end_date` |  | string | The end date of the interest rates to return in YYYY-MM-DD format. |

Example: `python fds.py /macro/interest-rates --bank <bank>`

### `GET /macro/interest-rates/banks`
Available central banks. Returns a list of available central bank codes for the interest rates endpoints. This endpoint is free and does not require authentication.

Example: `python fds.py /macro/interest-rates/banks `

### `GET /macro/interest-rates/snapshot`
Interest Rates (Real-Time). Get the current interest rates from all major central banks in the world.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `bank` | yes | string | The central bank code (e.g., FED, ECB, BOJ). Use the /macro/interest-rates/banks endpoint to get a list of available banks. |

Example: `python fds.py /macro/interest-rates/snapshot --bank <bank>`


## Market Data

### `GET /prices`
Get historical stock price data. Get end-of-day (EOD) historical price data for stocks.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` | yes | string | The stock ticker symbol (e.g. AAPL, MSFT). |
| `interval` | yes | day \| week \| month \| year | The time interval for the price data. |
| `start_date` | yes | string | The start date for the price data (format: YYYY-MM-DD). |
| `end_date` | yes | string | The end date for the price data (format: YYYY-MM-DD). |

Example: `python fds.py /prices --ticker <ticker> --interval <interval> --start_date <start_date> --end_date <end_date>`

### `GET /prices/snapshot`
Price Snapshot (Real-Time). Get the real-time price snapshot for a stock, including the current price, day change, and day change percent.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` | yes | string | The stock ticker symbol (e.g. AAPL, MSFT). |

Example: `python fds.py /prices/snapshot --ticker <ticker>`

### `GET /prices/snapshot/market`
Market Snapshot (Real-Time). Get the real-time price snapshot for the entire market. Requires an active subscription.

Example: `python fds.py /prices/snapshot/market `

### `GET /prices/snapshot/tickers`
Available tickers for price snapshots. Returns a list of available tickers for the price snapshot endpoint. This endpoint is free and does not require authentication.

Example: `python fds.py /prices/snapshot/tickers `

### `GET /prices/tickers`
Available tickers for price history. Returns a list of available tickers for the prices endpoint. This endpoint is free and does not require authentication.

Example: `python fds.py /prices/tickers `


## News

### `GET /news`
Get news articles. Get recent news articles for a specific company or the broad market. Pass a ticker for company-specific news, or omit the ticker for general market news. Articles are sourced from RSS feeds of publishers like The Motley Fool, Investing.com, Reuters, and more.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` |  | string | The ticker symbol of the company. Omit for broad market news. |
| `limit` |  | integer | The maximum number of news articles to return (default: 5, max: 10). |

Example: `python fds.py /news `


## SEC Filings

### `GET /filings`
Get SEC filings. Get SEC filings for a company.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `cik` |  | string | The Central Index Key (CIK) of the company. |
| `ticker` |  | string | The ticker symbol. |
| `filing_type` |  | array | Filter by one or more filing types. Repeat the query parameter to pass multiple values (e.g. filing_type=10-Q&filing_type=10-K). |
| `limit` |  | integer | The maximum number of filings to return (default: 10). |

Example: `python fds.py /filings `

### `GET /filings/ciks`
Available CIKs for SEC filings. Returns a list of available CIKs for the filings endpoint. This endpoint is free and does not require authentication.

Example: `python fds.py /filings/ciks `

### `GET /filings/items`
Get SEC filing items. Get the raw text Items from an SEC filing.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `ticker` | yes | string | The ticker symbol. |
| `filing_type` | yes | 10-K \| 10-Q \| 8-K | The type of filing. |
| `year` | yes | integer | The year of the filing. |
| `quarter` |  | integer | The quarter of the filing if 10-Q. |
| `item` |  | Item-1 \| Item-1A \| Item-1B \| Item-2 \| Item-3 \| Item-4 \| Item-5 \| Item-6 \| Item-7 \| Item-7A \| Item-8 \| Item-9 \| Item-9A \| Item-9B \| Item-10 \| Item-11 \| Item-12 \| Item-13 \| Item-14 \| Item-15 \| Item-16 \| Item-1.01 \| Item-1.02 \| Item-1.03 \| Item-1.04 \| Item-2.01 \| Item-2.02 \| Item-2.03 \| Item-2.04 \| Item-2.05 \| Item-2.06 \| Item-3.01 \| Item-3.02 \| Item-3.03 \| Item-4.01 \| Item-4.02 \| Item-5.01 \| Item-5.02 \| Item-5.03 \| Item-5.04 \| Item-5.05 \| Item-5.06 \| Item-5.07 \| Item-5.08 \| Item-6.01 \| Item-6.02 \| Item-6.03 \| Item-6.04 \| Item-6.05 \| Item-7.01 \| Item-8.01 \| Item-9.01 | The item to get. |
| `accession_number` |  | string | The accession number of the filing if 8-K. |
| `include_exhibits` |  | boolean | Whether to include the raw text from linked exhibits. Only applicable for 8-K filings. When true, exhibit objects will include the 'text' field containing the full exhibit content. |

Example: `python fds.py /filings/items --ticker <ticker> --filing_type <filing_type> --year <year>`

### `GET /filings/items/types`
Available filing item types. Returns a list of extractable item sections for 10-K, 10-Q, and 8-K filings. This endpoint is free and does not require authentication.

_query parameters:_

| name | required | type / values | description |
|------|----------|---------------|-------------|
| `filing_type` |  | string | Optional filter by filing type (e.g., 10-K, 10-Q). |

Example: `python fds.py /filings/items/types `

### `GET /filings/tickers`
Available tickers for SEC filings. Returns a list of available tickers for the filings endpoint. This endpoint is free and does not require authentication.

Example: `python fds.py /filings/tickers `

### `GET /filings/types`
Available SEC filing types. Returns a sorted list of valid SEC filing types (e.g., 10-K, 10-Q, 8-K). This endpoint is free and does not require authentication.

Example: `python fds.py /filings/types `

