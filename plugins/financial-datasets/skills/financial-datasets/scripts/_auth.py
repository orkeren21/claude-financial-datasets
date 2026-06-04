"""Resolve the Financial Datasets API key from the environment.

The skill itself ships no secret. The key is read at call-time from the first
of these that has a non-empty value:

  1. FINANCIAL_DATASETS_API_KEY  — a real environment variable (zero-config)
  2. ~/.claude/settings.json     — its `env.FINANCIAL_DATASETS_API_KEY` field.
                                   This is the cross-environment primary: Claude
                                   Code, Claude Desktop, and Cowork all read this
                                   file. We parse it directly so it works even
                                   where the harness doesn't inject env vars.
  3. ~/.financial-datasets/config.json — `{"api_key": "..."}` dedicated file.

If none is found, callers get a clear message pointing at the setup helper.
"""
import json
import os
from pathlib import Path

ENV_VAR = "FINANCIAL_DATASETS_API_KEY"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
CONFIG_PATH = Path.home() / ".financial-datasets" / "config.json"


class MissingKeyError(Exception):
    """Raised when no API key can be resolved from any source."""


def _clean(value):
    return value.strip() if isinstance(value, str) and value.strip() else None


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
        or _from_settings_json()
        or _from_config_json()
    )


def require_api_key():
    """Return the API key, or raise MissingKeyError with setup guidance."""
    key = resolve_api_key()
    if not key:
        raise MissingKeyError(
            "No Financial Datasets API key found.\n"
            "Set one up once (stored in ~/.claude/settings.json so every Claude "
            "environment can read it):\n"
            "    python scripts/setup_key.py YOUR_API_KEY\n"
            "or run the /fds-setup command. Get a key at "
            "https://www.financialdatasets.ai/."
        )
    return key
