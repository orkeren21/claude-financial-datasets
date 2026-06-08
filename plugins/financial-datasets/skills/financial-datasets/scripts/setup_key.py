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
