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
