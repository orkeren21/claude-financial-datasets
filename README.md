# Financial Datasets skill for Claude

A Claude skill + plugin that calls the [Financial Datasets API](https://docs.financialdatasets.ai)
directly — stock prices, company fundamentals (income statement, balance sheet,
cash flow, as-reported and segmented), financial metrics, earnings, SEC filings,
insider trades, institutional (13F) holdings, index/ETF holdings, KPIs, macro
interest rates, news, and a financial screener.

Calling the API directly (instead of via the Financial Datasets MCP server) lets
Claude **fan out many requests in parallel** and post-process the JSON freely.

## Install

```
/plugin marketplace add <github-user>/financial-datasets-skill
/plugin install financial-datasets
```

This works the same in Claude Code and Claude Desktop. (Until it's published to
GitHub you can add it from a local checkout with
`/plugin marketplace add /path/to/financial-datasets-skill`.)

## Set up your API key (once)

Get a key at <https://www.financialdatasets.ai/>, then:

```
/fds-setup
```

The key is stored in your `~/.claude/settings.json` `env` block — a file that
Claude Code, Claude Desktop, and Cowork all read — and verified with a test
call. **The key is never committed to this repo**; the skill ships no secret.

Key resolution order used by the skill:
1. `FINANCIAL_DATASETS_API_KEY` environment variable
2. `~/.claude/settings.json` → `env.FINANCIAL_DATASETS_API_KEY`
3. `~/.financial-datasets/config.json` → `{"api_key": "..."}`

## Use

Just ask. For example:
- "What's Apple's latest annual income statement and current share price?"
- "Compare revenue and net margin for MSFT, GOOGL, and AMZN over the last 3 years."
- "Show NVDA's recent insider trades and its latest 10-K."

Under the hood the skill calls `scripts/fds.py`. You can also run it directly:

```
python fds.py /prices/snapshot --ticker AAPL
python fds.py --list income            # discover endpoints
python fds.py --describe /prices       # see an endpoint's parameters
echo '[{"path":"/prices/snapshot","params":{"ticker":"AAPL"}}]' | python fds.py --batch -
```

## Layout

```
.claude-plugin/marketplace.json         # makes it installable in one command
plugins/financial-datasets/
├── .claude-plugin/plugin.json
├── commands/fds-setup.md               # /fds-setup
└── skills/financial-datasets/
    ├── SKILL.md
    ├── scripts/{fds.py, _auth.py, setup_key.py, openapi.json}
    └── references/endpoints.md          # full endpoint catalog
docs/                                    # design doc + endpoints generator
```

Regenerate the endpoint reference after a spec update with
`python docs/gen_endpoints.py`.

## License

MIT
