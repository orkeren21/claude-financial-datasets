# Project-local API key source — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `fds.py` read the Financial Datasets API key from a project-local file (`$FDS_KEY_FILE` or a `.fds_key` walked up from CWD) and let `setup_key.py --local` write it there, so Claude Cowork — whose sandbox can't reach `$HOME` — can both configure and use the skill.

**Architecture:** Two new key sources slot into `_auth.resolve_api_key()` above the existing `~`-based sources (explicit → project-local → home). `setup_key.py` gains a `--local` mode that writes the project-local file at `0600` and ensures a `.gitignore` ignores it. A new stdlib-`unittest` file, `scripts/test_auth.py`, locks the resolution order and the write-side behavior. All four docs that describe key resolution are updated, and the repo-root `.gitignore` learns `.fds_key`.

**Tech Stack:** Python 3 standard library only (`pathlib`, `json`, `os`, `argparse`, `unittest`). No third-party packages — the skill must run in any Claude environment without `pip install`.

**Spec:** `docs/2026-06-08-project-local-key-source-design.md`

**Working directory for all commands below:**
`plugins/financial-datasets/skills/financial-datasets/` (the folder holding `SKILL.md`; `scripts/` lives directly under it). Paths in this plan are relative to the repo root.

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `plugins/financial-datasets/skills/financial-datasets/scripts/_auth.py` | Modify (full rewrite) | Key resolution: add `$FDS_KEY_FILE` + `.fds_key` walk-up sources, ranked above `~`-based sources; updated docstring + `MissingKeyError` message. |
| `plugins/financial-datasets/skills/financial-datasets/scripts/setup_key.py` | Modify (full rewrite) | Add `--local` write mode (project-local file at `0600` + `.gitignore` management) alongside the unchanged default that writes `~/.claude/settings.json`. |
| `plugins/financial-datasets/skills/financial-datasets/scripts/test_auth.py` | Create | Stdlib `unittest` covering resolution precedence and the `--local` write side. Single entrypoint: `python scripts/test_auth.py`. |
| `plugins/financial-datasets/skills/financial-datasets/SKILL.md` | Modify | "First: make sure a key is configured" — add the new sources + the Cowork `--local` path. |
| `plugins/financial-datasets/commands/fds-setup.md` | Modify | Mention `--local` for sandboxed/Cowork use. |
| `README.md` | Modify | Update the resolution-order list + add a sandbox note. |
| `.gitignore` | Modify | Ignore `.fds_key` at the repo root. |

`fds.py` is **not** modified — it surfaces `MissingKeyError` text but needs no logic change.

**Note for the executor:** there is a second copy of these scripts under
`financial-datasets-workspace/skill-snapshot-iter1/scripts/`. That is a local eval
snapshot (the whole `*-workspace/` tree is git-ignored). **Do not touch it.**

---

## Task 1: Project-local key resolution in `_auth.py`

**Files:**
- Create: `plugins/financial-datasets/skills/financial-datasets/scripts/test_auth.py`
- Modify: `plugins/financial-datasets/skills/financial-datasets/scripts/_auth.py` (full rewrite)

- [ ] **Step 1: Write the failing resolution tests**

Create `plugins/financial-datasets/skills/financial-datasets/scripts/test_auth.py` with exactly this content:

```python
#!/usr/bin/env python3
"""Tests for the skill's API-key handling. Stdlib only:

    python scripts/test_auth.py                 # everything
    python scripts/test_auth.py ResolveKeyTest  # one class
"""
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _auth        # noqa: E402
import setup_key    # noqa: E402  (used by SetupLocalTest, added in Task 2)


class ResolveKeyTest(unittest.TestCase):
    def setUp(self):
        # A scratch working directory we control, with no .fds_key by default.
        self._cwd_tmp = TemporaryDirectory()
        self._origin = os.getcwd()
        os.chdir(self._cwd_tmp.name)

        # Point the home-based sources at files that do not exist, so the real
        # machine's key can never leak into the test.
        self._home_tmp = TemporaryDirectory()
        home = Path(self._home_tmp.name)
        self._patches = [
            mock.patch.object(_auth, "SETTINGS_PATH", home / "settings.json"),
            mock.patch.object(_auth, "CONFIG_PATH", home / "config.json"),
            mock.patch.dict(os.environ, {}, clear=True),  # tests opt into vars
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        os.chdir(self._origin)
        self._cwd_tmp.cleanup()
        self._home_tmp.cleanup()

    def _write(self, path, contents):
        Path(path).write_text(contents)

    def test_env_var_wins_over_everything(self):
        os.environ[_auth.ENV_VAR] = "env-key"
        explicit = Path.cwd() / "explicit"
        self._write(explicit, "explicit-key")
        os.environ[_auth.KEY_FILE_ENV] = str(explicit)
        self._write(Path.cwd() / _auth.KEY_FILENAME, "file-key")
        self.assertEqual(_auth.resolve_api_key(), "env-key")

    def test_key_file_env_resolves(self):
        target = Path.cwd() / "mykey"
        self._write(target, "explicit-key\n")
        os.environ[_auth.KEY_FILE_ENV] = str(target)
        self.assertEqual(_auth.resolve_api_key(), "explicit-key")

    def test_key_file_env_beats_walkup(self):
        explicit = Path.cwd() / "explicit"
        self._write(explicit, "explicit-key")
        os.environ[_auth.KEY_FILE_ENV] = str(explicit)
        self._write(Path.cwd() / _auth.KEY_FILENAME, "walkup-key")
        self.assertEqual(_auth.resolve_api_key(), "explicit-key")

    def test_fds_key_walkup_finds_parent(self):
        self._write(Path.cwd() / _auth.KEY_FILENAME, "walkup-key\n")
        nested = Path.cwd() / "a" / "b"
        nested.mkdir(parents=True)
        os.chdir(nested)
        self.assertEqual(_auth.resolve_api_key(), "walkup-key")

    def test_project_local_beats_settings(self):
        self._write(Path.cwd() / _auth.KEY_FILENAME, "walkup-key")
        self._write(_auth.SETTINGS_PATH,
                    '{"env": {"%s": "settings-key"}}' % _auth.ENV_VAR)
        self.assertEqual(_auth.resolve_api_key(), "walkup-key")

    def test_empty_key_file_falls_through(self):
        self._write(Path.cwd() / _auth.KEY_FILENAME, "   \n\n")
        self._write(_auth.SETTINGS_PATH,
                    '{"env": {"%s": "settings-key"}}' % _auth.ENV_VAR)
        self.assertEqual(_auth.resolve_api_key(), "settings-key")

    def test_missing_everything_raises(self):
        with self.assertRaises(_auth.MissingKeyError):
            _auth.require_api_key()


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

- [ ] **Step 2: Run the resolution tests to verify they fail**

Run:
```bash
cd plugins/financial-datasets/skills/financial-datasets
python scripts/test_auth.py ResolveKeyTest
```
Expected: FAIL — `AttributeError: module '_auth' has no attribute 'KEY_FILE_ENV'`
(the new constants/functions don't exist yet).

- [ ] **Step 3: Rewrite `_auth.py` with the new sources**

Replace the **entire contents** of `plugins/financial-datasets/skills/financial-datasets/scripts/_auth.py` with:

```python
"""Resolve the Financial Datasets API key from the environment.

The skill itself ships no secret. The key is read at call-time from the first
of these that has a non-empty value:

  1. FINANCIAL_DATASETS_API_KEY  — a real environment variable (zero-config).
  2. FDS_KEY_FILE                — path to a file whose contents are the key.
                                   An explicit, project-local override.
  3. .fds_key                    — a file found by walking up from the current
                                   directory to the filesystem root (like git
                                   finding .git). The project-local convention,
                                   and the only key store Claude Cowork's sandbox
                                   can reach, since it can't read $HOME.
  4. ~/.claude/settings.json     — its `env.FINANCIAL_DATASETS_API_KEY` field.
                                   The cross-environment primary for Claude Code
                                   and Claude Desktop.
  5. ~/.financial-datasets/config.json — `{"api_key": "..."}` dedicated file.

Project-local sources (2, 3) rank above the home-based ones (4, 5) so a project
can override a global key — the .env convention of local-beats-global.

If none is found, callers get a clear message pointing at the setup helper.
"""
import json
import os
from pathlib import Path

ENV_VAR = "FINANCIAL_DATASETS_API_KEY"
KEY_FILE_ENV = "FDS_KEY_FILE"
KEY_FILENAME = ".fds_key"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
CONFIG_PATH = Path.home() / ".financial-datasets" / "config.json"


class MissingKeyError(Exception):
    """Raised when no API key can be resolved from any source."""


def _clean(value):
    return value.strip() if isinstance(value, str) and value.strip() else None


def _read_key_file(path):
    """Return the first non-empty, stripped line of a key file, or None."""
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
    for directory in [cwd, *cwd.parents]:
        candidate = directory / KEY_FILENAME
        if candidate.is_file():
            key = _read_key_file(candidate)
            if key:
                return key
    return None


def _from_settings_json():
    try:
        data = json.loads(SETTINGS_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    env = data.get("env")
    if isinstance(env, dict):
        return _clean(env.get(ENV_VAR))
    return None


def _from_config_json():
    try:
        data = json.loads(CONFIG_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return _clean(data.get("api_key") or data.get("apiKey"))


def resolve_api_key():
    """Return the API key string, or None if no source has one."""
    return (
        _clean(os.environ.get(ENV_VAR))
        or _from_key_file_env()
        or _from_fds_key_walkup()
        or _from_settings_json()
        or _from_config_json()
    )


def require_api_key():
    """Return the API key, or raise MissingKeyError with setup guidance."""
    key = resolve_api_key()
    if not key:
        raise MissingKeyError(
            "No Financial Datasets API key found.\n"
            "Set one up once. On a normal machine (stored in "
            "~/.claude/settings.json so every Claude environment can read it):\n"
            "    python scripts/setup_key.py YOUR_API_KEY\n"
            "Inside a sandbox like Cowork (stored in a project-local .fds_key):\n"
            "    python scripts/setup_key.py YOUR_API_KEY --local\n"
            "or run the /fds-setup command. Get a key at "
            "https://www.financialdatasets.ai/."
        )
    return key
```

- [ ] **Step 4: Run the resolution tests to verify they pass**

Run:
```bash
python scripts/test_auth.py ResolveKeyTest
```
Expected: PASS — `Ran 7 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add plugins/financial-datasets/skills/financial-datasets/scripts/_auth.py \
        plugins/financial-datasets/skills/financial-datasets/scripts/test_auth.py
git commit -m "feat(auth): read API key from \$FDS_KEY_FILE / .fds_key walk-up

Adds two project-local key sources ranked above the ~-based sources so
Cowork's sandbox (no \$HOME access) can read a key from the mounted folder.
Covered by scripts/test_auth.py::ResolveKeyTest."
```

---

## Task 2: `--local` write mode in `setup_key.py`

**Files:**
- Modify: `plugins/financial-datasets/skills/financial-datasets/scripts/setup_key.py` (full rewrite)
- Modify: `plugins/financial-datasets/skills/financial-datasets/scripts/test_auth.py` (append a test class)

- [ ] **Step 1: Append the failing write-side tests**

Append this class to `scripts/test_auth.py`, immediately **before** the
`if __name__ == "__main__":` block:

```python
class SetupLocalTest(unittest.TestCase):
    def setUp(self):
        self._cwd_tmp = TemporaryDirectory()
        self._origin = os.getcwd()
        os.chdir(self._cwd_tmp.name)
        self._env = mock.patch.dict(os.environ, {}, clear=True)
        self._env.start()

    def tearDown(self):
        self._env.stop()
        os.chdir(self._origin)
        self._cwd_tmp.cleanup()

    def test_local_target_defaults_to_cwd(self):
        self.assertEqual(setup_key._local_target(),
                         (Path.cwd() / _auth.KEY_FILENAME).resolve())

    def test_local_target_honors_env(self):
        os.environ[_auth.KEY_FILE_ENV] = "custom_key_file"
        self.assertEqual(setup_key._local_target(),
                         (Path.cwd() / "custom_key_file").resolve())

    def test_store_key_local_writes_file_and_gitignore(self):
        path = setup_key.store_key_local("secret-key")
        self.assertEqual(Path(path).read_text().strip(), "secret-key")
        self.assertEqual(oct(Path(path).stat().st_mode & 0o777), "0o600")
        gitignore = Path(path).parent / ".gitignore"
        self.assertIn(".fds_key", gitignore.read_text().splitlines())

    def test_ensure_gitignored_appends_to_existing(self):
        gitignore = Path.cwd() / ".gitignore"
        gitignore.write_text("node_modules\n")
        setup_key._ensure_gitignored(Path.cwd() / _auth.KEY_FILENAME)
        lines = gitignore.read_text().splitlines()
        self.assertIn("node_modules", lines)
        self.assertIn(".fds_key", lines)

    def test_ensure_gitignored_idempotent(self):
        gitignore = Path.cwd() / ".gitignore"
        gitignore.write_text(".fds_key\n")
        setup_key._ensure_gitignored(Path.cwd() / _auth.KEY_FILENAME)
        self.assertEqual(gitignore.read_text().count(".fds_key"), 1)
```

- [ ] **Step 2: Run the write-side tests to verify they fail**

Run:
```bash
cd plugins/financial-datasets/skills/financial-datasets
python scripts/test_auth.py SetupLocalTest
```
Expected: FAIL — `AttributeError: module 'setup_key' has no attribute '_local_target'`.

- [ ] **Step 3: Rewrite `setup_key.py` with `--local`**

Replace the **entire contents** of `plugins/financial-datasets/skills/financial-datasets/scripts/setup_key.py` with:

```python
#!/usr/bin/env python3
"""Store the Financial Datasets API key for every Claude environment.

Default: writes `env.FINANCIAL_DATASETS_API_KEY` into ~/.claude/settings.json
(merging, so nothing else in your settings is touched), at 0600 perms.

--local: writes the key into a project-local file instead — $FDS_KEY_FILE if
set, otherwise ./.fds_key — at 0600 perms, and ensures a .gitignore beside it
ignores the file. Use this inside sandboxes like Cowork that can't reach $HOME.

Either way we make one cheap verification call so you know the key works before
you rely on it.

Usage:
    python setup_key.py YOUR_API_KEY              # ~/.claude/settings.json
    python setup_key.py YOUR_API_KEY --local      # ./.fds_key (or $FDS_KEY_FILE)
    python setup_key.py                           # interactive prompt (hidden)
    python setup_key.py --local                   # interactive + project-local

The key is never printed back and never written into the skill/repo.
"""
import argparse
import getpass
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _auth import ENV_VAR, KEY_FILE_ENV, KEY_FILENAME, SETTINGS_PATH  # noqa: E402


def store_key(key):
    """Merge the key into ~/.claude/settings.json at 0600. Returns the path."""
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if SETTINGS_PATH.exists():
        try:
            data = json.loads(SETTINGS_PATH.read_text())
        except json.JSONDecodeError:
            sys.exit(f"{SETTINGS_PATH} is not valid JSON — fix or remove it, then retry.")
    if not isinstance(data, dict):
        sys.exit(f"{SETTINGS_PATH} does not contain a JSON object.")

    env = data.get("env")
    if not isinstance(env, dict):
        env = {}
    env[ENV_VAR] = key
    data["env"] = env

    tmp = SETTINGS_PATH.with_name(SETTINGS_PATH.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    os.chmod(tmp, 0o600)
    tmp.replace(SETTINGS_PATH)
    try:
        os.chmod(SETTINGS_PATH, 0o600)
    except OSError:
        pass
    return SETTINGS_PATH


def _local_target():
    """Where --local writes: $FDS_KEY_FILE if set, else ./.fds_key (absolute)."""
    env_path = os.environ.get(KEY_FILE_ENV, "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()
    return (Path.cwd() / KEY_FILENAME).resolve()


def _ensure_gitignored(target):
    """Make sure a .gitignore beside `target` ignores target's basename."""
    gitignore = target.parent / ".gitignore"
    entry = target.name
    if gitignore.exists():
        lines = gitignore.read_text().splitlines()
        if entry in (ln.strip() for ln in lines):
            return  # already ignored
        with gitignore.open("a") as fh:
            if lines and lines[-1].strip():
                fh.write("\n")
            fh.write(entry + "\n")
        print(f"Appended '{entry}' to {gitignore}.")
    else:
        gitignore.write_text(entry + "\n")
        print(f"Created {gitignore} ignoring '{entry}'.")


def store_key_local(key):
    """Write the key to the project-local target at 0600, gitignored. Returns path."""
    target = _local_target()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(key + "\n")
    try:
        os.chmod(target, 0o600)
    except OSError:
        pass
    _ensure_gitignored(target)
    return target


def verify(key):
    from fds import call, load_spec  # local import; fds.py sits next to us
    return call("/prices/snapshot", params={"ticker": "AAPL"}, key=key, spec=load_spec())


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="setup_key.py",
        description="Store the Financial Datasets API key.")
    parser.add_argument("key", nargs="?",
                        help="The API key (omit for a hidden interactive prompt).")
    parser.add_argument("--local", action="store_true",
                        help="Write a project-local .fds_key (or $FDS_KEY_FILE) "
                             "instead of ~/.claude/settings.json. For sandboxes "
                             "like Cowork that can't reach $HOME.")
    args = parser.parse_args(argv)

    key = (args.key.strip() if args.key
           else getpass.getpass("Financial Datasets API key: ").strip())
    if not key:
        sys.exit("No key provided.")

    if args.local:
        path = store_key_local(key)
        print(f"Stored key in {path} (chmod 0600).")
    else:
        path = store_key(key)
        print(f"Stored key in {path} (env.{ENV_VAR}).")

    print("Verifying with a test call to /prices/snapshot?ticker=AAPL ...")
    result = verify(key)
    if result.get("ok"):
        snap = result.get("data") or {}
        print("Verified — the key works. Sample response:")
        print(json.dumps(snap, indent=2, default=str)[:600])
    else:
        print(f"WARNING: stored, but the verification call failed: {result.get('error')}")
        sys.exit(2)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the write-side tests to verify they pass**

Run:
```bash
python scripts/test_auth.py SetupLocalTest
```
Expected: PASS — `Ran 5 tests ... OK`.

- [ ] **Step 5: Run the full suite**

Run:
```bash
python scripts/test_auth.py
```
Expected: PASS — `Ran 12 tests ... OK` (7 resolution + 5 write-side).

- [ ] **Step 6: Commit**

```bash
git add plugins/financial-datasets/skills/financial-datasets/scripts/setup_key.py \
        plugins/financial-datasets/skills/financial-datasets/scripts/test_auth.py
git commit -m "feat(setup): add --local to write a git-ignored .fds_key

setup_key.py --local writes the key to \$FDS_KEY_FILE or ./.fds_key at 0600
and ensures a .gitignore covers it, then verifies — so Cowork can configure
the key without \$HOME access. Covered by test_auth.py::SetupLocalTest."
```

---

## Task 3: Documentation + repo `.gitignore`

**Files:**
- Modify: `plugins/financial-datasets/skills/financial-datasets/SKILL.md`
- Modify: `plugins/financial-datasets/commands/fds-setup.md`
- Modify: `README.md`
- Modify: `.gitignore`

- [ ] **Step 1: Update `SKILL.md`**

In `plugins/financial-datasets/skills/financial-datasets/SKILL.md`, replace this block:

```markdown
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
```

with:

```markdown
## First: make sure a key is configured

The API is keyed and metered. `fds.py` finds the key automatically from the first
of these that is set: the `FINANCIAL_DATASETS_API_KEY` env var, a file named in
`$FDS_KEY_FILE`, a `.fds_key` file in the working directory or any parent,
`~/.claude/settings.json`'s `env` block, or `~/.financial-datasets/config.json`.
If a call comes back with an error about a missing key, run setup once and
continue:

```
python scripts/setup_key.py "THE_USERS_KEY"
```

This stores the key in `~/.claude/settings.json` (which Claude Code and Claude
Desktop read) and verifies it with a test call.

**In a sandbox like Cowork** that can't reach the home directory, store the key in
the mounted project folder instead — `fds.py` reads it back via the `.fds_key`
lookup:

```
python scripts/setup_key.py "THE_USERS_KEY" --local
```

That writes `./.fds_key` (or `$FDS_KEY_FILE` if set), keeps it at 0600, and adds it
to `.gitignore`. Ask the user for their key if you don't have it; never write a key
into a repo or echo it back.
```

- [ ] **Step 2: Update `commands/fds-setup.md`**

In `plugins/financial-datasets/commands/fds-setup.md`, replace this block:

```markdown
2. Run the setup helper, passing the key as the argument:

   ```
   python <financial-datasets skill dir>/scripts/setup_key.py "THE_KEY"
   ```

   The helper writes `env.FINANCIAL_DATASETS_API_KEY` into
   `~/.claude/settings.json` (merging — it preserves everything else and keeps
   the file at 0600 perms), then makes one verification call to confirm the key
   works.
```

with:

```markdown
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
```

- [ ] **Step 3: Update `README.md`**

In `README.md`, replace this block:

```markdown
The key is stored in your `~/.claude/settings.json` `env` block — a file that
Claude Code, Claude Desktop, and Cowork all read — and verified with a test
call. **The key is never committed to this repo**; the skill ships no secret.

Key resolution order used by the skill:
1. `FINANCIAL_DATASETS_API_KEY` environment variable
2. `~/.claude/settings.json` → `env.FINANCIAL_DATASETS_API_KEY`
3. `~/.financial-datasets/config.json` → `{"api_key": "..."}`
```

with:

```markdown
The key is stored in your `~/.claude/settings.json` `env` block — a file that
Claude Code and Claude Desktop read — and verified with a test call. **The key is
never committed to this repo**; the skill ships no secret.

Key resolution order used by the skill (first match wins):
1. `FINANCIAL_DATASETS_API_KEY` environment variable
2. `$FDS_KEY_FILE` → a file whose contents are the key
3. `.fds_key` in the working directory or any parent directory
4. `~/.claude/settings.json` → `env.FINANCIAL_DATASETS_API_KEY`
5. `~/.financial-datasets/config.json` → `{"api_key": "..."}`

**Sandboxed environments (Cowork).** A sandbox that can't reach your home
directory can't use the `~/.claude/settings.json` or `~/.financial-datasets`
sources. Store the key in the mounted project folder instead with
`python .../setup_key.py YOUR_KEY --local`, which writes a git-ignored `.fds_key`
(source 3).
```

- [ ] **Step 4: Update the repo-root `.gitignore`**

In `.gitignore`, replace this block:

```
# Never commit secrets or local key stores
.env
*.env
config.json
**/config.json
.financial-datasets/
secrets*
*api*key*
*.key
```

with:

```
# Never commit secrets or local key stores
.env
*.env
.fds_key
**/.fds_key
config.json
**/config.json
.financial-datasets/
secrets*
*api*key*
*.key
```

- [ ] **Step 5: Verify the edits landed and nothing regressed**

Run:
```bash
cd plugins/financial-datasets/skills/financial-datasets
python scripts/test_auth.py
cd -
git check-ignore .fds_key
grep -c -- "--local" plugins/financial-datasets/skills/financial-datasets/SKILL.md \
                     plugins/financial-datasets/commands/fds-setup.md README.md
grep -c "FDS_KEY_FILE" README.md
```
Expected:
- tests `Ran 12 tests ... OK`
- `git check-ignore .fds_key` prints `.fds_key` (exit 0 — it's ignored now)
- each `--local` grep count is `>= 1`
- `FDS_KEY_FILE` grep count is `>= 1`

- [ ] **Step 6: Commit**

```bash
git add plugins/financial-datasets/skills/financial-datasets/SKILL.md \
        plugins/financial-datasets/commands/fds-setup.md \
        README.md .gitignore
git commit -m "docs: document \$FDS_KEY_FILE / .fds_key key source and --local setup

Updates SKILL.md, /fds-setup, and README resolution order; ignores .fds_key
at the repo root."
```

---

## Manual smoke test (after all tasks)

Confirms the end-to-end Cowork path on a real machine, from a throwaway dir:

```bash
SKILL=$(pwd)/plugins/financial-datasets/skills/financial-datasets
TMP=$(mktemp -d) && cd "$TMP"
python "$SKILL/scripts/setup_key.py" "YOUR_REAL_KEY" --local   # writes ./.fds_key + .gitignore, verifies
ls -l .fds_key .gitignore                                       # .fds_key is -rw------- ; .gitignore lists it
python "$SKILL/scripts/fds.py" /prices/snapshot --ticker AAPL  # resolves the key via .fds_key walk-up
cd - && rm -rf "$TMP"
```
Expected: setup prints "Verified — the key works", and the `fds.py` call returns
`"ok": true` with snapshot data — proving write (`--local`) and read (walk-up)
agree without any `$HOME`-based source.

---

## Self-Review

**Spec coverage:**
- Resolution order (explicit → project-local → home) → Task 1 (`_auth.py` rewrite + `ResolveKeyTest`). ✅
- File format (first non-empty line, stripped; empty falls through) → `_read_key_file` + `test_empty_key_file_falls_through`. ✅
- `.fds_key` walk-up to root → `_from_fds_key_walkup` + `test_fds_key_walkup_finds_parent`. ✅
- `$FDS_KEY_FILE` explicit path → `_from_key_file_env` + `test_key_file_env_resolves` / `test_key_file_env_beats_walkup`. ✅
- `MissingKeyError` mentions `--local` → Task 1 message + `test_missing_everything_raises`. ✅
- `setup_key.py --local` target ($FDS_KEY_FILE else ./.fds_key), 0600, prints absolute path → Task 2 (`store_key_local`/`_local_target`). ✅
- Gitignore create-or-append (basename, idempotent) → `_ensure_gitignored` + 3 tests. ✅
- Verification call retained → `verify()` unchanged, called in both branches. ✅
- Default behavior unchanged → `store_key()` kept; default branch in `main`. ✅
- Tests = stdlib unittest, single entrypoint → `scripts/test_auth.py`. ✅
- Docs (4 places) + repo `.gitignore` → Task 3. ✅

**Placeholder scan:** No TBD/TODO/"handle errors"/"similar to". Every code and doc step shows full content. ✅

**Type/name consistency:** `KEY_FILE_ENV`, `KEY_FILENAME`, `_read_key_file`, `_from_key_file_env`, `_from_fds_key_walkup`, `store_key_local`, `_local_target`, `_ensure_gitignored` are defined in `_auth.py`/`setup_key.py` and referenced with identical names in `test_auth.py` and later tasks. `resolve_api_key`/`require_api_key`/`MissingKeyError`/`ENV_VAR`/`SETTINGS_PATH`/`CONFIG_PATH` keep their existing names, so `fds.py`'s `from _auth import require_api_key, MissingKeyError` stays valid. ✅
```
