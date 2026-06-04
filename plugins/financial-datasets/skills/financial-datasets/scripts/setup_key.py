#!/usr/bin/env python3
"""Store the Financial Datasets API key once, for every Claude environment.

Writes `env.FINANCIAL_DATASETS_API_KEY` into ~/.claude/settings.json (merging,
so nothing else in your settings is touched), keeps the file at 0600 perms, then
makes one cheap verification call so we know the key actually works before you
rely on it.

Usage:
    python setup_key.py YOUR_API_KEY      # non-interactive (what the agent uses)
    python setup_key.py                   # interactive prompt (input hidden)

The key is never printed back and never written into the skill/repo.
"""
import getpass
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _auth import ENV_VAR, SETTINGS_PATH  # noqa: E402


def store_key(key):
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


def verify(key):
    from fds import call, load_spec  # local import; fds.py sits next to us
    return call("/prices/snapshot", params={"ticker": "AAPL"}, key=key, spec=load_spec())


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    key = argv[0].strip() if argv else getpass.getpass("Financial Datasets API key: ").strip()
    if not key:
        sys.exit("No key provided.")

    store_key(key)
    print(f"Stored key in {SETTINGS_PATH} (env.{ENV_VAR}).")

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
