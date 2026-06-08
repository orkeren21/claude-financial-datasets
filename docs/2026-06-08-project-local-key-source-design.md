# Project-local API key source for `fds.py`

**Date:** 2026-06-08
**Status:** Approved design, pending implementation
**Scope:** `plugins/financial-datasets/skills/financial-datasets/scripts/{_auth.py,setup_key.py}`, `SKILL.md`, `commands/fds-setup.md`, `README.md`, new `scripts/test_auth.py`

## Problem

`fds.py` resolves the Financial Datasets API key from three sources, all under the
user's home directory:

1. `FINANCIAL_DATASETS_API_KEY` env var
2. `~/.claude/settings.json` → `env.FINANCIAL_DATASETS_API_KEY`
3. `~/.financial-datasets/config.json`

Claude Cowork runs the skill inside a sandbox that **cannot read the user's real
home directory**, so sources #2 and #3 are unreachable. `setup_key.py` writes into
`~/.claude/settings.json`, so even running setup from inside Cowork doesn't help —
the file it writes can't be read back. The one thing Cowork *can* read and write is
a **mounted project folder**.

## Goals

- Let `fds.py` read the key from a project-local file that lives in the mounted
  folder Cowork can access.
- Let `setup_key.py` *write* that project-local file, so the key can be configured
  entirely from inside Cowork (not just read).
- Keep the change small, standard-library-only, and backward compatible: every
  existing source and the existing `setup_key.py` default behavior keep working.

## Non-goals

- No change to the HTTP/calling logic in `fds.py`.
- No new dependencies.
- No attempt to auto-detect the Cowork mount path. Location is driven by CWD
  walk-up and an explicit `$FDS_KEY_FILE`, which covers the mount case.

## Resolution order (new)

Explicit → project-local → home-based. The two new sources (2, 3) slot in
**above** the home-based sources, so a project can override a global key — the
`.env` convention of local-beats-global. (On a normal dev machine this is the only
place ordering matters; inside Cowork the home sources are unreachable anyway. The
key/file lives in the project-local dir, so it must win.)

| # | Source | New? |
|---|--------|------|
| 1 | `FINANCIAL_DATASETS_API_KEY` env var | no |
| 2 | `$FDS_KEY_FILE` — explicit path to a file containing the key | **yes** |
| 3 | `.fds_key` found by walking up from CWD to filesystem root | **yes** |
| 4 | `~/.claude/settings.json` → `env.FINANCIAL_DATASETS_API_KEY` | no |
| 5 | `~/.financial-datasets/config.json` → `api_key`/`apiKey` | no |

### File format

Raw token. Read the file, take the **first non-empty line**, `.strip()` it.
Tolerates a trailing newline. No JSON, no `KEY=value` parsing. An empty or
unreadable file is skipped silently (falls through to the next source), matching
the existing `_clean()` behavior.

### `.fds_key` walk-up

Starting at `Path.cwd()`, check that directory and each parent up to and including
the filesystem root (`[cwd, *cwd.parents]`). The first readable, non-empty
`.fds_key` wins. This mirrors how git locates `.git`, so the key resolves whether
the command runs from the mount root or a subdirectory of it.

**Known limitation (documented, not fixed):** if `fds.py` is run from the skill's
own directory and the key file lives in a *separate* mounted folder that is not an
ancestor of CWD, the walk-up won't find it. `$FDS_KEY_FILE` is the explicit escape
hatch for that case, and the docs will say so.

### Read implementation sketch (`_auth.py`)

```python
KEY_FILE_ENV = "FDS_KEY_FILE"
KEY_FILENAME = ".fds_key"

def _read_key_file(path):
    try:
        text = Path(path).read_text()
    except OSError:
        return None
    for line in text.splitlines():
        cleaned = _clean(line)
        if cleaned:
            return cleaned
    return None

def _from_key_file_env():
    path = _clean(os.environ.get(KEY_FILE_ENV))
    return _read_key_file(path) if path else None

def _from_fds_key_walkup():
    cwd = Path.cwd()
    for d in [cwd, *cwd.parents]:
        candidate = d / KEY_FILENAME
        if candidate.is_file():
            key = _read_key_file(candidate)
            if key:
                return key
    return None

def resolve_api_key():
    return (
        _clean(os.environ.get(ENV_VAR))
        or _from_key_file_env()
        or _from_fds_key_walkup()
        or _from_settings_json()
        or _from_config_json()
    )
```

The `MissingKeyError` message gains a one-line mention of the project-local option
(`--local` / `.fds_key`) alongside the existing setup guidance.

## Write side — `setup_key.py --local`

Default behavior is unchanged (writes `~/.claude/settings.json`). A new `--local`
flag writes the project-local file instead:

```
python scripts/setup_key.py YOUR_KEY --local
```

Behavior:

1. **Target path:** `$FDS_KEY_FILE` if set, otherwise `./.fds_key` (CWD).
2. Write the raw key to the target; `chmod 0600`.
3. **Print the absolute path written**, so it's unambiguous which file holds the key.
4. **Gitignore management** (user-approved): in the *parent directory of the target
   file*, ensure a `.gitignore` ignores the key file's basename.
   - If `.gitignore` exists and doesn't already contain the basename as a line,
     append it.
   - If `.gitignore` doesn't exist, create it containing the basename.
   - Print whether it was created or appended. This is harmless even outside a git
     repo and protects the secret if the dir later becomes one.
5. Run the existing verification call (`/prices/snapshot?ticker=AAPL`) and report,
   exactly as the default path does today.

Interactive mode (`setup_key.py` with no key arg) still prompts for the key; if
`--local` is passed it routes the prompted key to the local target.

## Security

- `.fds_key` is a plaintext secret on disk. Mitigations: `chmod 0600`, automatic
  `.gitignore` entry, and never echoing the key back (unchanged from today).
- The skill repo's own root `.gitignore` should also list `.fds_key` so a stray key
  dropped at the repo root during testing can't be committed.

## Tests — `scripts/test_auth.py`

New stdlib-`unittest` file, no dependencies, run with `python scripts/test_auth.py`.
Written first (TDD), covering `resolve_api_key()` precedence with `monkeypatch`-style
env/cwd manipulation via `unittest.mock.patch.dict` and `tmp` directories:

- `FINANCIAL_DATASETS_API_KEY` env var beats every file source.
- `$FDS_KEY_FILE` resolves a key from an explicit path.
- `.fds_key` walk-up finds a file in a parent directory of CWD.
- `$FDS_KEY_FILE` beats `.fds_key` walk-up.
- Project-local sources beat `~/.claude/settings.json` (point the home-based
  lookups at temp paths so the test is hermetic).
- Empty / whitespace-only key file falls through to the next source.
- No source set → `require_api_key()` raises `MissingKeyError`.

## Docs to update

Keep all four key-resolution descriptions truthful:

- `_auth.py` module docstring — the numbered source list.
- `SKILL.md` → "First: make sure a key is configured" — add the project-local
  source and the `--local` setup path, with a one-line note for Cowork/sandboxed
  environments.
- `commands/fds-setup.md` — mention `--local` for sandboxed/Cowork use.
- `README.md` — update if it documents key setup.

## Verification

- `python scripts/test_auth.py` passes.
- Manual: from a temp dir, `python .../setup_key.py KEY --local`, confirm `.fds_key`
  written at 0600, `.gitignore` updated, verification call succeeds, then a plain
  `python .../fds.py /prices/snapshot --ticker AAPL` run from that dir resolves the
  key via walk-up.
```
