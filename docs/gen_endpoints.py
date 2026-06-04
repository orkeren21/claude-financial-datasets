#!/usr/bin/env python3
"""Generate references/endpoints.md from the bundled OpenAPI spec.

Re-run this whenever the spec changes:
    python docs/gen_endpoints.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "docs" / "fds-openapi.json"
OUT = ROOT / "plugins" / "financial-datasets" / "skills" / "financial-datasets" / "references" / "endpoints.md"

spec = json.loads(SPEC.read_text())


def resolve(node):
    if isinstance(node, dict) and "$ref" in node:
        cur = spec
        for part in node["$ref"].lstrip("#/").split("/"):
            cur = cur.get(part, {})
        return cur
    return node


def params_for(op):
    rows = []
    for prm in op.get("parameters", []) or []:
        prm = resolve(prm)
        if not prm.get("name"):
            continue
        sch = prm.get("schema", {}) or {}
        typ = sch.get("type", "")
        if sch.get("enum"):
            typ = " \\| ".join(str(e) for e in sch["enum"])
        rows.append((prm["name"], "yes" if prm.get("required") else "", typ,
                     (prm.get("description") or "").replace("\n", " ").strip()))
    return rows


def body_for(op):
    rb = op.get("requestBody")
    if not rb:
        return []
    rb = resolve(rb)
    schema = resolve(((rb.get("content") or {}).get("application/json") or {}).get("schema") or {})
    required = set(schema.get("required", []))
    rows = []
    for name, prop in (schema.get("properties") or {}).items():
        prop = resolve(prop)
        typ = prop.get("type", "")
        if prop.get("enum"):
            typ = " \\| ".join(str(e) for e in prop["enum"])
        rows.append((name, "yes" if name in required else "", typ,
                     (prop.get("description") or "").replace("\n", " ").strip()))
    return rows


# group by first tag, else by first path segment
groups = {}
for path, node in spec["paths"].items():
    for method in ("get", "post"):
        if method not in node:
            continue
        op = node[method]
        tag = (op.get("tags") or [path.strip("/").split("/")[0]])[0]
        groups.setdefault(tag, []).append((method.upper(), path, op))

lines = []
lines.append("# Financial Datasets API — endpoint reference\n")
lines.append(f"Base URL: `https://api.financialdatasets.ai` · Auth header: `X-API-KEY` · "
             f"{sum(len(v) for v in groups.values())} endpoints\n")
lines.append("All calls go through `scripts/fds.py`. For a GET, every parameter below is a "
             "`--flag value`. For the two POST endpoints, pass the body with `--json '{...}'`.\n")

# table of contents
lines.append("## Contents\n")
for tag in sorted(groups):
    anchor = tag.lower().replace(" ", "-").replace("&", "")
    lines.append(f"- [{tag}](#{anchor}) ({len(groups[tag])})")
lines.append("")

for tag in sorted(groups):
    lines.append(f"\n## {tag}\n")
    for method, path, op in sorted(groups[tag], key=lambda x: x[1]):
        lines.append(f"### `{method} {path}`")
        if op.get("summary"):
            lines.append(f"{op['summary']}. {op.get('description', '')}".strip())
        rows = params_for(op) if method == "GET" else body_for(op)
        if rows:
            label = "query parameters" if method == "GET" else "JSON body fields"
            lines.append(f"\n_{label}:_\n")
            lines.append("| name | required | type / values | description |")
            lines.append("|------|----------|---------------|-------------|")
            for name, req, typ, desc in rows:
                lines.append(f"| `{name}` | {req} | {typ} | {desc} |")
        # example
        if method == "GET":
            ex_params = " ".join(
                f"--{n} <{n}>" for n, req, *_ in rows if req == "yes"
            ) or ""
            lines.append(f"\nExample: `python fds.py {path} {ex_params}`".rstrip() + "\n")
        else:
            lines.append(f"\nExample: `python fds.py {path} --json '{{...}}'`\n")

OUT.write_text("\n".join(lines) + "\n")
print(f"Wrote {OUT} ({len(lines)} lines)")
