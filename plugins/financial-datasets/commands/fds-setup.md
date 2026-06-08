---
description: Store your Financial Datasets API key so every Claude environment can use it
---

The user wants to set up their Financial Datasets API key for the
`financial-datasets` skill.

Do this:

1. Ask the user for their Financial Datasets API key if they haven't already
   provided it in the conversation. They can find or create one at
   https://www.financialdatasets.ai/ (account → API keys). Treat the key as a
   secret: do not echo it back, log it, or write it into any file in a repo.

2. Run the setup helper, passing the key as the argument:

   ```
   python <financial-datasets skill dir>/scripts/setup_key.py "THE_KEY"
   ```

   The helper writes `env.FINANCIAL_DATASETS_API_KEY` into
   `~/.claude/settings.json` (merging — it preserves everything else and keeps
   the file at 0600 perms), then makes one verification call to confirm the key
   works.

   **In a sandbox like Cowork** that can't read the user's home directory, add
   `--local` so the key is written to the mounted project folder instead:

   ```
   python <financial-datasets skill dir>/scripts/setup_key.py "THE_KEY" --local
   ```

   That writes `./.fds_key` (or `$FDS_KEY_FILE` if set) at 0600 and adds it to
   `.gitignore`. The same `fds.py` calls then read it back automatically.

3. Report the result. If verification succeeded, tell the user they're ready —
   the default setup makes the key work in Claude Code and Claude Desktop, while
   `--local` makes it work in the current sandbox such as Cowork. If it failed
   with an auth error, the key is wrong — ask them to double-check it. If it
   failed with a payment error, their credit is exhausted.
