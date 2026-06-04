#!/usr/bin/env python3
"""Generic command-line caller for the Financial Datasets API.

One tool covers every endpoint. It picks GET or POST automatically from the
bundled OpenAPI spec, sends the X-API-KEY header, retries transient failures,
and can fire many requests concurrently — the main reason to call the API
directly instead of through the MCP server.

Standard library only, so it runs in any Claude environment without `pip install`.

EXAMPLES
  # Single GET; any --flag becomes a query parameter
  python fds.py /prices/snapshot --ticker AAPL
  python fds.py /financials/income-statements --ticker MSFT --period annual --limit 4

  # A POST endpoint; pass the JSON body with --json (method auto-detected)
  python fds.py /financials/search/screener --json '{"period":"ttm","limit":10,
      "filters":[{"field":"revenue","operator":"gt","value":100000000000}]}'

  # Concurrent batch — the parallelism win. Reads a JSON array of requests.
  echo '[{"path":"/prices/snapshot","params":{"ticker":"AAPL"},"label":"AAPL"},
         {"path":"/prices/snapshot","params":{"ticker":"MSFT"},"label":"MSFT"}]' \
    | python fds.py --batch -

  # Discovery
  python fds.py --list income          # list endpoints whose path contains "income"
  python fds.py --describe /prices     # show parameters for an endpoint
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _auth import require_api_key, MissingKeyError  # noqa: E402

BASE_URL = "https://api.financialdatasets.ai"
SPEC_PATH = Path(__file__).with_name("openapi.json")
# Endpoints that are POST even if the bundled spec is missing.
POST_PATHS = {"/financials/search/screener", "/financials/search/line-items"}
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 4  # total attempts for transient (429 / 5xx / network) failures


def load_spec():
    try:
        return json.loads(SPEC_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def norm_path(path):
    return path if path.startswith("/") else "/" + path


def method_for(path, spec):
    path = norm_path(path)
    if path in POST_PATHS:
        return "POST"
    if spec:
        node = spec.get("paths", {}).get(path)
        if isinstance(node, dict):
            if "get" in node:
                return "GET"
            if "post" in node:
                return "POST"
    return "GET"


def _parse_error(body, code):
    """Turn an error response body into the clearest message we can."""
    msg = body
    try:
        parsed = json.loads(body)
        if isinstance(parsed, dict):
            msg = parsed.get("message") or parsed.get("error") or parsed.get("detail") or body
    except (json.JSONDecodeError, TypeError):
        pass
    hints = {
        401: "Unauthorized — the API key is missing or invalid. Re-run /fds-setup.",
        402: "Payment required — your Financial Datasets credit is exhausted. "
             "Top up at https://www.financialdatasets.ai/.",
        404: "Not found — check the ticker/CIK and that this endpoint path is correct.",
    }
    hint = hints.get(code)
    return f"{msg} ({hint})" if hint else msg


def call(path, params=None, method=None, key=None, base=BASE_URL,
         spec=None, timeout=DEFAULT_TIMEOUT, json_body=None):
    """Make one API call. Returns a dict; never raises for HTTP errors.

    Shape: {"ok": bool, "status": int|None, "path": str, "data"|"error": ...}
    """
    path = norm_path(path)
    params = params or {}
    if method is None:
        method = method_for(path, spec)
    method = method.upper()

    try:
        key = key or require_api_key()
    except MissingKeyError as exc:
        return {"ok": False, "status": None, "path": path, "error": str(exc)}

    headers = {"X-API-KEY": key, "Accept": "application/json"}
    url = base.rstrip("/") + path
    data = None

    if method == "GET":
        query = {k: v for k, v in params.items() if v is not None and v != ""}
        if query:
            url += "?" + urllib.parse.urlencode(query, doseq=True)
    else:
        body_obj = json_body if json_body is not None else params
        headers["Content-Type"] = "application/json"
        data = json.dumps(body_obj).encode()

    last = None
    for attempt in range(MAX_RETRIES):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
                return {
                    "ok": True,
                    "status": getattr(resp, "status", 200),
                    "path": path,
                    "data": json.loads(raw) if raw else None,
                }
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            if exc.code == 429 or 500 <= exc.code < 600:
                last = (exc.code, body)
                time.sleep(2 ** attempt)  # exponential backoff
                continue
            return {"ok": False, "status": exc.code, "path": path,
                    "error": _parse_error(body, exc.code)}
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last = (None, str(exc))
            time.sleep(2 ** attempt)
            continue

    code, body = last if last else (None, "request failed")
    return {"ok": False, "status": code, "path": path,
            "error": _parse_error(str(body), code)}


def run_batch(requests_list, key, spec, concurrency, timeout):
    """Run a list of request dicts concurrently, preserving input order."""
    def one(item):
        result = call(
            item["path"],
            params=item.get("params"),
            method=item.get("method"),
            key=key,
            spec=spec,
            timeout=timeout,
            json_body=item.get("json"),
        )
        result["label"] = item.get("label", item["path"])
        return result

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        return list(pool.map(one, requests_list))


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_params(extras):
    """Fold leftover `--name value` / `--name=value` tokens into a dict.

    Repeated names collect into a list (handy for multi-ticker query params).
    A flag with no following value becomes "".
    """
    params = {}
    i = 0
    while i < len(extras):
        tok = extras[i]
        if not tok.startswith("--"):
            i += 1
            continue
        name = tok[2:]
        if "=" in name:
            name, value = name.split("=", 1)
        elif i + 1 < len(extras) and not extras[i + 1].startswith("--"):
            value = extras[i + 1]
            i += 1
        else:
            value = ""
        if name in params:
            if isinstance(params[name], list):
                params[name].append(value)
            else:
                params[name] = [params[name], value]
        else:
            params[name] = value
        i += 1
    return params


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="fds.py", add_help=True,
        description="Generic caller for the Financial Datasets API.")
    parser.add_argument("path", nargs="?", help="Endpoint path, e.g. /prices/snapshot")
    parser.add_argument("--method", choices=["get", "post", "GET", "POST"],
                        help="Force the HTTP method (auto-detected otherwise).")
    parser.add_argument("--json", dest="json_body",
                        help="JSON request body for POST endpoints.")
    parser.add_argument("--batch", help="Run a JSON array of requests concurrently "
                                        "('-' reads stdin).")
    parser.add_argument("--concurrency", type=int, default=5,
                        help="Max concurrent requests in batch mode (default 5).")
    parser.add_argument("--base", default=BASE_URL, help="Override the base URL.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help="Per-request timeout in seconds (default 30).")
    parser.add_argument("--compact", action="store_true",
                        help="Compact JSON output (default is pretty-printed).")
    parser.add_argument("--list", nargs="?", const="", metavar="FILTER",
                        help="List endpoint paths (optionally filtered by substring).")
    parser.add_argument("--describe", metavar="PATH",
                        help="Show the parameters for an endpoint.")
    args, extras = parser.parse_known_args(argv)

    spec = load_spec()

    def emit(obj):
        print(json.dumps(obj, indent=None if args.compact else 2, default=str))

    # --- discovery modes (no key / network needed) ---
    if args.list is not None:
        if not spec:
            sys.exit("OpenAPI spec not bundled; see references/endpoints.md instead.")
        needle = args.list.lower()
        paths = sorted(p for p in spec.get("paths", {}) if needle in p.lower())
        for p in paths:
            m = method_for(p, spec)
            node = spec["paths"][p].get(m.lower(), {})
            print(f"{m:4} {p}  — {node.get('summary', '')}")
        return

    if args.describe:
        if not spec:
            sys.exit("OpenAPI spec not bundled; see references/endpoints.md instead.")
        emit(_describe(args.describe, spec))
        return

    # --- batch mode ---
    if args.batch:
        text = sys.stdin.read() if args.batch == "-" else Path(args.batch).read_text()
        try:
            items = json.loads(text)
        except json.JSONDecodeError as exc:
            sys.exit(f"--batch input is not valid JSON: {exc}")
        if not isinstance(items, list):
            sys.exit("--batch input must be a JSON array of request objects.")
        try:
            key = require_api_key()
        except MissingKeyError as exc:
            sys.exit(str(exc))
        emit(run_batch(items, key, spec, args.concurrency, args.timeout))
        return

    # --- single call ---
    if not args.path:
        parser.error("provide an endpoint path, or use --batch / --list / --describe")

    params = parse_params(extras)
    json_body = json.loads(args.json_body) if args.json_body else None
    result = call(args.path, params=params, method=args.method, base=args.base,
                  spec=spec, timeout=args.timeout, json_body=json_body)
    emit(result)
    if not result["ok"]:
        sys.exit(1)


def _resolve_ref(ref, spec):
    node = spec
    for part in ref.lstrip("#/").split("/"):
        node = node.get(part, {})
    return node


def _describe(path, spec):
    path = norm_path(path)
    node = spec.get("paths", {}).get(path)
    if not node:
        return {"error": f"Unknown path {path}. Try --list."}
    method = method_for(path, spec)
    op = node.get(method.lower(), {})
    out = {"path": path, "method": method, "summary": op.get("summary"),
           "description": op.get("description"), "parameters": []}
    for prm in op.get("parameters", []) or []:
        if "$ref" in prm:
            prm = _resolve_ref(prm["$ref"], spec)
        if not prm.get("name"):
            continue
        schema = prm.get("schema", {})
        out["parameters"].append({
            "name": prm.get("name"),
            "required": bool(prm.get("required")),
            "type": schema.get("type"),
            "enum": schema.get("enum"),
            "description": prm.get("description"),
        })
    return out


if __name__ == "__main__":
    main()
