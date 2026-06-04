# Financial Datasets API Skill — Design

**Date:** 2026-06-04
**Status:** Approved, building via skill-creator

## Goal

A Claude skill that calls the [Financial Datasets API](https://docs.financialdatasets.ai)
directly (instead of via its MCP server), so Claude can fan out parallel calls,
manipulate responses freely, and cover the full endpoint surface. Must run in
**Claude Code, Claude Desktop, and Cowork (cloud sessions)**, and be **shareable**
(public plugin, each user bringing their own key).

## API facts (from the OpenAPI spec)

- **Base URL:** `https://api.financialdatasets.ai/`
- **Auth:** a single `X-API-KEY` HTTP header (apiKey scheme — no OAuth/signing)
- **49 endpoints** across ~13 groups: financials (income / balance / cash-flow,
  as-reported, segments), financial-metrics (+ snapshot), prices (+ snapshot),
  earnings, filings (+ items), insider-trades, institutional-holdings, KPIs
  (guidance / metrics / non-gaap), index-funds, company facts, news,
  macro/interest-rates, and a line-item screener.
- **Metered** against the user's credit ($20 balance) → cost-awareness matters.

## Security principle

The **skill is 100% public and secret-free**. The **API key never enters the repo**.
The key is resolved from the user's environment at call-time. A `.gitignore`
blocks `.env`, `config.json`, and key-like files as defense-in-depth.

## Key resolution (the crux)

A shared `_auth.py` resolves the key in this order, first non-empty wins:

1. `FINANCIAL_DATASETS_API_KEY` real environment variable (zero-config power users)
2. `~/.claude/settings.json` → `env.FINANCIAL_DATASETS_API_KEY` ← **cross-environment primary**
3. `~/.financial-datasets/config.json` → `api_key` (optional dedicated file)

Why #2 is primary: Claude Code, Claude Desktop, and **Cowork all read
`~/.claude/settings.json`**. The script parses the JSON file directly rather than
relying on the harness to inject the value as a real env var — so it works even
in environments that don't auto-inject. (`settings.json` is already `chmod 600`.)

If no key is found, the script exits with a clear message telling Claude to run
the setup helper.

## Components

```
financial-datasets-skill/                 # public repo (publish when proven)
├── .claude-plugin/marketplace.json       # one-command installable marketplace
├── plugins/financial-datasets/
│   ├── .claude-plugin/plugin.json        # plugin manifest
│   ├── commands/fds-setup.md             # /fds-setup → runs setup_key.py
│   └── skills/financial-datasets/
│       ├── SKILL.md                      # lean; pushy triggers; parallel + cost guidance
│       ├── scripts/
│       │   ├── fds.py                    # generic caller for ALL 49 endpoints + batch/parallel
│       │   ├── _auth.py                  # shared key resolution
│       │   └── setup_key.py              # merge key into settings.json + verify call
│       └── references/endpoints.md       # all 49 endpoints, params, examples (from OpenAPI)
└── README.md                             # install + key setup
```

### `fds.py` — one generic caller, not 49 functions
- `python fds.py <path> --param value …` → `GET {base}/<path>?…` with `X-API-KEY`.
- 429 retry with backoff; clear error surfacing; JSON output.
- **Batch/parallel mode:** accepts a list of requests (stdin / `--batch`) and runs
  them concurrently (thread pool), returning an array. This is the parallelism
  advantage over the MCP.

### `setup_key.py`
- Accepts key (arg or prompt), merges into `~/.claude/settings.json` `env` block
  (read-modify-write; preserves all existing config; keeps 600 perms), then makes
  one cheap verification call (e.g. a single-ticker price snapshot) to prove it works.

### `SKILL.md`
- Triggers aggressively on financial-data intent (prices, fundamentals, income
  statement / balance sheet / cash flow, SEC filings 10-K/10-Q/8-K, earnings,
  insider trades, 13F holdings, KPIs, metrics, screener) even when the API isn't named.
- Instructs: resolve key (run `/fds-setup` if missing); use `fds.py`; **fan out
  parallel calls** for multi-ticker / multi-period asks; point to
  `references/endpoints.md` for the full surface; be **cost-aware** (metered — batch,
  avoid redundant pulls, prefer snapshot endpoints).

## Installation (target UX)
```
/plugin marketplace add <user>/financial-datasets-skill
/plugin install financial-datasets
/fds-setup   # paste key once → stored in ~/.claude/settings.json → verified
```

## Testing plan (skill-creator phase, live API with user's key)
1. Single-company fundamentals + current price (e.g. Apple).
2. 3-ticker multi-year revenue & net-margin comparison (exercises parallelism).
3. Insider trades + latest 10-K filing for one ticker.

## Decisions log
- Public plugin + universal key contract (rejected: personal-only skill; MCP-only).
- Build locally first; publish to a new public GitHub repo once proven.
- Cowork key path: `~/.claude/settings.json` env block (user-confirmed Cowork reads it),
  with real env var honored and a dedicated config file as fallback.
