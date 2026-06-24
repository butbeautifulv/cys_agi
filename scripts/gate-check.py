#!/usr/bin/env python3
"""Evaluate scan reports against security-gate-policy.yaml."""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SEVERITY_ORDER = {"note": 0, "none": 0, "info": 1, "low": 2, "medium": 3, "high": 4, "critical": 5, "error": 5}


def load_policy_section(path: Path, control: str) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_section = False
    section: dict = {}
    indent = None
    for line in lines:
        if re.match(rf"^{re.escape(control)}:\s*$", line):
            in_section = True
            indent = len(line) - len(line.lstrip())
            continue
        if not in_section:
            continue
        if line.strip() and not line.startswith(" ") and not line.startswith("\t"):
            break
        m = re.match(r"^\s+(\w+):\s*(.+)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                section[key] = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
            elif val in ("true", "false"):
                section[key] = val == "true"
            else:
                section[key] = val.strip("'\"")
    defaults = {}
    in_defaults = False
    for line in lines:
        if line.strip() == "defaults:":
            in_defaults = True
            continue
        if in_defaults:
            if line.strip() and not line.startswith(" "):
                break
            m = re.match(r"^\s+(\w+):\s*(.+)$", line)
            if m:
                key, val = m.group(1), m.group(2).strip()
                if val.startswith("[") and val.endswith("]"):
                    defaults[key] = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
    section.setdefault("mode", "warn")
    section.setdefault("severity_block", defaults.get("severity_block", ["critical", "high"]))
    section.setdefault("severity_warn", defaults.get("severity_warn", ["medium"]))
    return section


def normalize_level(level: str) -> str:
    return (level or "note").lower().replace("warning", "medium").replace("error", "high")


def parse_sarif(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    levels: list[str] = []
    for run in data.get("runs", []):
        for result in run.get("results", []):
            levels.append(normalize_level(result.get("level", "note")))
    return levels


def parse_gitlab_secrets(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    levels: list[str] = []
    for vuln in data.get("vulnerabilities", data.get("secrets", [])):
        sev = normalize_level(vuln.get("severity", "high"))
        levels.append(sev)
    if data.get("total") or data.get("secret_detection"):
        levels.append("high")
    return levels


def parse_zap_baseline(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    levels: list[str] = []
    risk_map = {"3": "high", "2": "medium", "1": "low", "0": "info"}
    for site in data.get("site", []):
        for alert in site.get("alerts", []):
            code = str(alert.get("riskcode", alert.get("risk", "1")))
            levels.append(risk_map.get(code, normalize_level(alert.get("riskdesc", "medium"))))
    return levels


def parse_junit(path: Path) -> list[str]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    root = ET.parse(path).getroot()
    levels: list[str] = []
    suites = [root] if root.tag == "testsuite" else root.findall(".//testsuite")
    for suite in suites:
        for _ in range(int(suite.attrib.get("errors", "0") or "0")):
            levels.append("critical")
        for _ in range(int(suite.attrib.get("failures", "0") or "0")):
            levels.append("high")
        for case in suite.findall("testcase"):
            if case.find("error") is not None:
                levels.append("critical")
            elif case.find("failure") is not None:
                levels.append("high")
    return levels


def check_artifact(path: Path, policy: dict, label: str) -> tuple[bool, str]:
    mode = policy.get("mode", "warn")
    if not path.exists() or path.stat().st_size == 0:
        msg = f"missing or empty {label}: {path}"
        if mode == "block":
            return False, msg
        if policy.get("required_on_main") and mode == "warn":
            return True, f"warn — {msg}"
        return True, f"warn — {msg}" if mode == "warn" else msg
    return True, f"{label} present ({path.stat().st_size} bytes)"


def check_ml_data(path: Path, policy: dict) -> tuple[bool, str]:
    if not path.exists():
        return True, "no ml_data report (clean or no datasets)"
    levels = parse_report(path)
    # PII findings emitted as error/high — block when mode=block
    if policy.get("block_pii"):
        high = [l for l in levels if l in ("high", "critical", "error")]
        if high and policy.get("mode") == "block":
            return False, f"PII or blocking ml_data findings: {len(high)}"
    return evaluate(levels, policy)


def check_sbom_artifact(path: Path, policy: dict) -> tuple[bool, str]:
    return check_artifact(path, policy, "SBOM")


def check_sec_func_tests(path: Path, policy: dict) -> tuple[bool, str]:
    mode = policy.get("mode", "warn")
    if not path.exists():
        return True, "no sec-func report (tests skipped or passed)"
    levels = parse_report(path)
    return evaluate(levels, policy)


def parse_report(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    data = json.loads(text)
    levels = [normalize_level(r.get("level", "note")) for r in data.get("runs", [{}])[0].get("results", [])]
    if levels:
        return levels
    if "runs" in data:
        return parse_sarif(path)
    if "vulnerabilities" in data or "secrets" in data:
        return parse_gitlab_secrets(path)
    if isinstance(data, list):
        return [normalize_level(x.get("severity", "high")) for x in data]
    return []


def evaluate(levels: list[str], policy: dict) -> tuple[bool, str]:
    mode = policy.get("mode", "warn")
    if mode in ("info", "optional", "artifact"):
        return True, f"mode={mode}, gate skipped"

    block_set = {normalize_level(s) for s in policy.get("severity_block", ["critical", "high"])}
    warn_set = {normalize_level(s) for s in policy.get("severity_warn", ["medium"])}

    blocking = [l for l in levels if l in block_set]
    warning = [l for l in levels if l in warn_set]

    if blocking:
        msg = f"blocking findings: {blocking}"
        if mode == "block":
            return False, msg
        return True, f"warn only — {msg}"

    if warning and mode == "block":
        return True, f"warnings only: {warning}"

    return True, "ok"


def main() -> None:
    p = argparse.ArgumentParser(description="Security gate check")
    p.add_argument("--control", required=True)
    p.add_argument("--report", required=True, type=Path)
    p.add_argument("--policy", default="config/security-gate-policy.yaml", type=Path)
    args = p.parse_args()

    if not args.policy.exists():
        print(f"Policy not found: {args.policy}", file=sys.stderr)
        sys.exit(2)

    control = args.control
    if control == "container":
        control = "sca"

    policy = load_policy_section(args.policy, control)

    if args.control == "sbom":
        ok, msg = check_sbom_artifact(args.report, policy)
    elif args.control in ("ml_bom", "aibom"):
        ok, msg = check_artifact(args.report, policy, args.control)
    elif args.control == "ml_data":
        ok, msg = check_ml_data(args.report, policy)
    elif args.control == "dast":
        levels = parse_zap_baseline(args.report) if args.report.exists() else []
        ok, msg = evaluate(levels, policy)
    elif args.control == "iast":
        levels = parse_zap_baseline(args.report) if args.report.exists() else []
        ok, msg = evaluate(levels, policy)
    elif args.control == "fuzzing":
        levels = parse_junit(args.report) if args.report.exists() else []
        ok, msg = evaluate(levels, policy)
    elif args.control == "binary_fuzz":
        levels = parse_junit(args.report) if args.report.exists() else []
        ok, msg = evaluate(levels, policy)
    elif args.control == "sec_func_tests":
        ok, msg = check_sec_func_tests(args.report, policy)
    else:
        levels = parse_report(args.report) if args.report.exists() else []
        ok, msg = evaluate(levels, policy)

    findings = 0
    if args.control == "sbom":
        findings = 1 if args.report.exists() else 0
    elif args.control == "dast" and args.report.exists():
        findings = len(parse_zap_baseline(args.report))
    elif args.control == "iast" and args.report.exists():
        findings = len(parse_zap_baseline(args.report))
    elif args.control == "fuzzing" and args.report.exists():
        findings = len(parse_junit(args.report))
    elif args.control == "binary_fuzz" and args.report.exists():
        findings = len(parse_junit(args.report))
    elif args.control not in ("sbom", "dast", "iast", "fuzzing", "binary_fuzz"):
        findings = len(parse_report(args.report)) if args.report.exists() else 0
    print(f"[{args.control}] {msg} (findings={findings}, mode={policy.get('mode')})")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
