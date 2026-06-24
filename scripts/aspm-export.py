#!/usr/bin/env python3
"""Export scan reports to ASPM/ASOC platforms (DefectDojo, noop)."""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


def expand_env(value: str) -> str:
    """Expand ${VAR:-default} patterns using os.environ."""

    def repl(match: re.Match[str]) -> str:
        body = match.group(1)
        if ":-" in body:
            name, default = body.split(":-", 1)
            return os.environ.get(name, default)
        return os.environ.get(body, "")

    return re.sub(r"\$\{([^}]+)\}", repl, value)


def load_config(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text) or {}
    return _parse_config_simple(text)


def _parse_config_simple(text: str) -> dict:
    """Minimal YAML subset when PyYAML is unavailable."""
    cfg: dict = {"controls": {}}
    section = None
    control = None
    for line in text.splitlines():
        if line.strip().startswith("#") or not line.strip():
            continue
        if re.match(r"^[a-z_]+:\s*$", line):
            section = line.split(":")[0]
            if section == "controls":
                cfg.setdefault("controls", {})
            continue
        m = re.match(r"^  (\w+):\s*(.+)$", line)
        if m and section == "defectdojo":
            key, val = m.group(1), m.group(2).strip().strip("'\"")
            cfg.setdefault("defectdojo", {})[key] = val in ("true", "false") if val in ("true", "false") else val
        m2 = re.match(r"^  (\w+):\s*$", line)
        if m2 and section == "controls":
            control = m2.group(1)
            cfg["controls"][control] = {}
        m3 = re.match(r"^    (\w+):\s*(.+)$", line)
        if m3 and section == "controls" and control:
            cfg["controls"][control][m3.group(1)] = m3.group(2).strip().strip("'\"")
    top = re.match(r"^(backend):\s*(.+)$", text)
    if top:
        cfg["backend"] = top.group(2).strip()
    return cfg


def is_enabled(cfg: dict) -> bool:
    env_name = (cfg.get("defaults") or {}).get("enabled_env", "DEFECTDOJO_URL")
    return bool(os.environ.get(env_name, "").strip())


def report_has_findings(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return True
    if "runs" in data:
        for run in data.get("runs", []):
            if run.get("results"):
                return True
        return False
    if "site" in data:
        for site in data.get("site", []):
            if site.get("alerts"):
                return True
        return False
    if data.get("vulnerabilities") or data.get("Results"):
        return True
    return path.stat().st_size > 50


def build_multipart(fields: dict[str, str], file_field: str, file_path: Path) -> tuple[bytes, str]:
    boundary = f"----aspm-{uuid.uuid4().hex}"
    lines: list[bytes] = []
    for key, val in fields.items():
        if val is None or val == "":
            continue
        lines.append(f"--{boundary}\r\n".encode())
        lines.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        lines.append(f"{val}\r\n".encode())
    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    lines.append(f"--{boundary}\r\n".encode())
    lines.append(
        f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'.encode()
    )
    lines.append(f"Content-Type: {mime}\r\n\r\n".encode())
    lines.append(file_path.read_bytes())
    lines.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(lines)
    return body, f"multipart/form-data; boundary={boundary}"


def export_defectdojo(cfg: dict, control: str, report: Path, dry_run: bool) -> tuple[bool, str]:
    dd = cfg.get("defectdojo") or {}
    ctrl = (cfg.get("controls") or {}).get(control)
    if not ctrl:
        return False, f"unknown control: {control}"

    url_base = os.environ.get("DEFECTDOJO_URL", "").rstrip("/")
    token = os.environ.get("DEFECTDOJO_API_TOKEN", "")
    if not url_base:
        return True, "skip — DEFECTDOJO_URL not set"
    if not token and not dry_run:
        return True, "skip — DEFECTDOJO_API_TOKEN not set"

    endpoint = "reimport-scan" if dd.get("reimport", True) else "import-scan"
    api_url = f"{url_base}/api/v2/{endpoint}/"

    fields = {
        "scan_type": ctrl.get("scan_type", "SARIF"),
        "test_title": ctrl.get("test_title", control),
        "product_name": expand_env(str(dd.get("product_name", "app"))),
        "engagement_name": expand_env(str(dd.get("engagement_name", "CI/CD"))),
        "commit_hash": expand_env(str(dd.get("commit_hash", ""))),
        "branch_tag": expand_env(str(dd.get("branch_tag", ""))),
        "build_id": expand_env(str(dd.get("build_id", ""))),
        "minimum_severity": str(dd.get("minimum_severity", "Info")),
        "auto_create_context": "true" if dd.get("auto_create_context", True) else "false",
        "close_old_findings": "true" if dd.get("close_old_findings", False) else "false",
        "active": "true",
        "verified": "false",
    }

    if dry_run:
        return True, f"dry-run POST {api_url} control={control} scan_type={fields['scan_type']}"

    body, content_type = build_multipart(fields, "file", report)
    req = Request(
        api_url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Token {token}",
            "Content-Type": content_type,
        },
    )
    try:
        with urlopen(req, timeout=120) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
            return True, f"uploaded ({resp.status}): {payload[:200]}"
    except HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        return False, f"HTTP {e.code}: {detail}"
    except URLError as e:
        return False, f"network error: {e.reason}"


def main() -> None:
    p = argparse.ArgumentParser(description="Export findings to ASPM/ASOC")
    p.add_argument("--control", required=True)
    p.add_argument("--report", required=True, type=Path)
    p.add_argument("--config", default="config/aspm-export.yaml", type=Path)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--skip-empty", action="store_true", help="Skip upload when report has no findings")
    args = p.parse_args()

    if not args.config.exists():
        print(f"Config not found: {args.config}", file=sys.stderr)
        sys.exit(2)

    cfg = load_config(args.config)
    backend = cfg.get("backend", "defectdojo")

    if not is_enabled(cfg):
        print(f"[aspm] skip — {cfg.get('defaults', {}).get('enabled_env', 'DEFECTDOJO_URL')} not set")
        sys.exit(0)

    if not args.report.exists():
        print(f"[aspm] skip — report missing: {args.report}")
        sys.exit(0)

    if args.skip_empty and not report_has_findings(args.report):
        print(f"[aspm] skip — empty report: {args.report}")
        sys.exit(0)

    if backend == "noop":
        print(f"[aspm] noop backend — would export {args.control} from {args.report}")
        sys.exit(0)

    if backend == "defectdojo":
        ok, msg = export_defectdojo(cfg, args.control, args.report, args.dry_run)
    else:
        print(f"[aspm] unknown backend: {backend}", file=sys.stderr)
        sys.exit(2)

    print(f"[aspm:{args.control}] {msg}")
    fail_on_error = os.environ.get("DEFECTDOJO_FAIL_ON_ERROR", "false").lower() == "true"
    if not ok and fail_on_error:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
