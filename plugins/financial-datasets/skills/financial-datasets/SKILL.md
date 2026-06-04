---
name: financial-datasets
description: >-
  Call the Financial Datasets API directly for real, current data on public
  companies. Use this whenever the user asks about stock prices or price history,
  company fundamentals or financials (income statement, balance sheet, cash flow —
  including as-reported and segmented), financial metrics and ratios, valuation
  inputs, earnings (results, estimates, surprises), SEC filings (10-K, 10-Q, 8-K)
  and their sections, insider trades (Form 4), institutional holdings (13F),
  index/ETF holdings, company facts, KPIs and management guidance, financial news,
  macro interest rates, or wants to screen or filter stocks by financial criteria —
  even when they don't name "Financial Datasets" or any API. Prefer this over the
  Financial Datasets MCP server: it fans out many requests in parallel and lets you
  post-process the JSON freely. Needs a one-time API key setup (/fds-setup).
---

# Financial Datasets API

Direct access to the [Financial Datasets API](https://docs.financialdatasets.ai)
(`https://api.financialdatasets.ai`) for fundamentals, prices, filings, and more.
Everything goes through one script — `scripts/fds.py` — which handles auth,
retries, and concurrent batches. No third-party packages are required.

Paths below are relative to this skill's directory. If your shell is elsewhere,
use the absolute path to `scripts/fds.py` (the directory holding this SKILL.md).

## First: make sure a key is configured

The API is keyed and metered. `fds.py` finds the key automatically from (in
order) the `FINANCIAL_DATASETS_API_KEY` env var, `~/.claude/settings.json`'s
`env` block, or `~/.financial-datasets/config.json`. If a call comes back with
an error about a missing key, run setup once and continue:

```
python scripts/setup_key.py "THE_USERS_KEY"
```

This stores the key in `~/.claude/settings.json` (which Claude Code, Claude
Desktop, and Cowork all read) and verifies it with a test call. Ask the user for
their key if you don't have it; never write a key into a repo or echo it back.

## Making calls

**Single GET** — every endpoint parameter is just a `--flag`:

```
python fds.py /prices/snapshot --ticker AAPL
python fds.py /financials/income-statements --ticker MSFT --period annual --limit 4
python fds.py /prices --ticker NVDA --interval day --start_date 2024-01-01 --end_date 2024-03-31
```

**POST endpoints** (`/financials/search/screener`, `/financials/search/line-items`)
take a JSON body; the method is auto-detected:

```
python fds.py /financials/search/screener --json '{"limit":10,"filters":[{"field":"revenue","operator":"gt","value":100000000000}]}'
```

Each call prints `{"ok": ..., "status": ..., "data" | "error": ...}`. On failure
the `error` is a plain-English message (bad key, exhausted credit, unknown
ticker, etc.), and the exit code is non-zero.

## Fan out in parallel — this is the point

When a request spans **multiple tickers, statements, or periods**, don't make
serial calls. Send a JSON array to batch mode and they run concurrently:

```
echo '[
  {"path":"/financials/income-statements","params":{"ticker":"MSFT","period":"annual","limit":3},"label":"MSFT"},
  {"path":"/financials/income-statements","params":{"ticker":"GOOGL","period":"annual","limit":3},"label":"GOOGL"},
  {"path":"/financials/income-statements","params":{"ticker":"AMZN","period":"annual","limit":3},"label":"AMZN"}
]' | python fds.py --batch - --concurrency 5
```

Output is an array of results in input order, each tagged with its `label`.
Reach for batch mode for peer comparisons, portfolio sweeps, and any
"compare/across/each of these" request.

## Common endpoints (use these directly — no lookup needed)

These cover almost every real request. The path and key parameters are here so you
can call straight away instead of spending a round-trip on discovery.

| Want | Path | Method | Key parameters |
|------|------|--------|----------------|
| Current price | `/prices/snapshot` | GET | `ticker`* |
| Price history (EOD) | `/prices` | GET | `ticker`* · `interval`* (`day`\|`week`\|`month`\|`year`) · `start_date`* · `end_date`* |
| Income statement | `/financials/income-statements` | GET | `ticker`*† · `period`* · `limit` |
| Balance sheet | `/financials/balance-sheets` | GET | `ticker`*† · `period`* · `limit` |
| Cash flow statement | `/financials/cash-flow-statements` | GET | `ticker`*† · `period`* · `limit` |
| Ratios & metrics (incl. `net_margin`, P/E, ROE, etc.) | `/financial-metrics` | GET | `ticker`*† · `period`* · `limit` |
| Current metrics snapshot | `/financial-metrics/snapshot` | GET | `ticker`*† |
| Insider trades (Form 4, newest first) | `/insider-trades` | GET | `ticker`* · `limit` |
| SEC filings | `/filings` | GET | `ticker`*† · `filing_type` (e.g. `10-K`, `10-Q`, `8-K`) · `limit` |
| Earnings | `/earnings` | GET | `ticker`* · `limit` |
| News | `/news` | GET | `ticker` · `limit` |
| Company facts | `/company/facts` | GET | `ticker`*† |
| Screen/filter stocks | `/financials/search/screener` | POST | body: `filters`* `[{field, operator, value}]` · `limit` |

`*` = required · `†` = supply `ticker` **or** `cik`. `period` is `annual` \| `quarterly`
\| `ttm`. The financials/metrics endpoints also accept date filters
`report_period`, `report_period_gte`, `report_period_lte`, `report_period_gt`,
`report_period_lt` (YYYY-MM-DD). Screener `operator` is one of
`gt`/`lt`/`gte`/`lte`/`eq`/`in`. Prefer `/financial-metrics` (which returns
`net_margin`, etc., pre-computed) over recomputing ratios from raw statements.

## Anything else (the long tail)

For endpoints not in the table above — segmented or as-reported financials, KPIs,
institutional holdings, index funds, macro interest rates, line-item search, the
`/tickers` and `/types` helper lists — discover them on demand (one call, only when
needed):

- `python fds.py --list <substring>` — list matching endpoint paths.
- `python fds.py --describe /some/path` — show an endpoint's exact parameters
  (authoritative; also use this if a cheat-sheet call ever returns a parameter error).
- `references/endpoints.md` — the full catalog of all 49 endpoints with a table of
  contents, if you want to browse.

## Spend the credit deliberately

The user's balance is finite. Be economical:

- Pull only what the question needs; prefer `limit` to bound results.
- Use `snapshot` endpoints (`/prices/snapshot`, `/financial-metrics/snapshot`)
  for "current" values instead of fetching full history.
- Don't re-request data you already have in the conversation.
- Batch related calls rather than looping one ticker at a time.

## Presenting results

Parse the JSON and answer the actual question — a clean table or a few numbers,
not a raw dump. Include the period/date and ticker so figures are unambiguous,
and note when data is missing rather than inventing it.
