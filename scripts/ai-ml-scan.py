#!/usr/bin/env python3
"""Lightweight AI/ML security scanners — SARIF/JSON output for gate-check.py."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

PII_PATTERNS = [
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "email"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "ssn"),
    (re.compile(r"\b\+?\d{10,15}\b"), "phone"),
]

SKILL_SUSPICIOUS = [
    re.compile(r"ignore\s+previous\s+instructions", re.I),
    re.compile(r"system\s*:\s*you\s+are", re.I),
    re.compile(r"eval\s*\(", re.I),
    re.compile(r"exec\s*\(", re.I),
    re.compile(r"__import__", re.I),
]

MCP_SUSPICIOUS = [
    re.compile(r"rm\s+-rf", re.I),
    re.compile(r"curl\s+.*\|\s*bash", re.I),
    re.compile(r"subprocess", re.I),
]


def sarif_from_findings(findings: list[dict]) -> dict:
    results = []
    for f in findings:
        results.append(
            {
                "level": f.get("level", "warning"),
                "message": {"text": f.get("message", "finding")},
                "locations": [{"physicalLocation": {"artifactLocation": {"uri": f.get("file", ".")}}}],
            }
        )
    return {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "ai-ml-scan"}}, "results": results}]}


def write_sarif(path: Path, findings: list[dict]) -> None:
    path.write_text(json.dumps(sarif_from_findings(findings), indent=2), encoding="utf-8")


def scan_skills(root: Path) -> list[dict]:
    findings: list[dict] = []
    for base in (root / ".cursor" / "skills", root / ".agents" / "skills"):
        if not base.exists():
            continue
        for skill in base.rglob("SKILL.md"):
            text = skill.read_text(encoding="utf-8", errors="replace")
            for pat in SKILL_SUSPICIOUS:
                if pat.search(text):
                    findings.append(
                        {
                            "level": "warning",
                            "message": f"suspicious pattern in skill: {pat.pattern}",
                            "file": str(skill.relative_to(root)),
                        }
                    )
    return findings


def scan_mcp(root: Path) -> list[dict]:
    findings: list[dict] = []
    candidates = list(root.glob("**/mcp*.json")) + list((root / ".cursor").glob("mcp.json"))
    for cfg in candidates:
        if not cfg.is_file():
            continue
        text = cfg.read_text(encoding="utf-8", errors="replace")
        for pat in MCP_SUSPICIOUS:
            if pat.search(text):
                findings.append(
                    {
                        "level": "warning",
                        "message": f"suspicious MCP config: {pat.pattern}",
                        "file": str(cfg.relative_to(root)),
                    }
                )
    return findings


def scan_ml_data(root: Path) -> list[dict]:
    findings: list[dict] = []
    for pattern in ("data/**", "datasets/**"):
        for path in root.glob(pattern):
            if not path.is_file() or path.suffix.lower() not in (".csv", ".txt", ".tsv"):
                continue
            try:
                with path.open(encoding="utf-8", errors="replace") as fh:
                    sample = fh.read(65536)
            except OSError:
                continue
            for rx, kind in PII_PATTERNS:
                if rx.search(sample):
                    findings.append(
                        {
                            "level": "error",
                            "message": f"PII detected ({kind}) in {path.name}",
                            "file": str(path.relative_to(root)),
                        }
                    )
    return findings


def scan_pickle(root: Path) -> list[dict]:
    findings: list[dict] = []
    for path in root.rglob("*"):
        if path.suffix.lower() in (".pkl", ".pickle") and path.is_file():
            findings.append(
                {
                    "level": "warning",
                    "message": f"pickle artifact present: {path.name}",
                    "file": str(path.relative_to(root)),
                }
            )
    return findings


def generate_aibom(root: Path, out: Path) -> None:
    components = []
    for skill in (root / ".agents" / "skills").rglob("SKILL.md"):
        components.append({"type": "skill", "name": skill.parent.name, "path": str(skill)})
    for m in root.glob("**/mcp*.json"):
        components.append({"type": "mcp", "name": m.name, "path": str(m)})
    out.write_text(json.dumps({"specVersion": "1.0", "components": components}, indent=2), encoding="utf-8")


def generate_ml_bom(root: Path, out: Path) -> None:
    models = [str(p.relative_to(root)) for p in root.rglob("*") if p.suffix.lower() in (".pkl", ".onnx", ".pt", ".h5")]
    datasets = [str(p.relative_to(root)) for p in root.glob("data/**/*") if p.is_file()]
    out.write_text(
        json.dumps({"mlBomVersion": "1.0", "models": models, "datasets": datasets}, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["skill_scan", "mcp_scan", "ml_data", "pickle_scan", "aibom", "ml_bom"])
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--report", type=Path, default=Path("report.sarif"))
    args = p.parse_args()

    if args.mode == "skill_scan":
        write_sarif(args.report, scan_skills(args.root))
    elif args.mode == "mcp_scan":
        write_sarif(args.report, scan_mcp(args.root))
    elif args.mode == "ml_data":
        write_sarif(args.report, scan_ml_data(args.root))
    elif args.mode == "pickle_scan":
        write_sarif(args.report, scan_pickle(args.root))
    elif args.mode == "aibom":
        generate_aibom(args.root, args.report)
    elif args.mode == "ml_bom":
        generate_ml_bom(args.root, args.report)
    sys.exit(0)


if __name__ == "__main__":
    main()
