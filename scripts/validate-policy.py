#!/usr/bin/env python3
"""Validate security-gate-policy.yaml structure."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED = {
    "defaults": ["severity_block"],
    "secrets": ["mode"],
    "sast": ["mode", "severity_block"],
    "osa": ["mode"],
    "sca": ["mode"],
    "iac": ["mode", "paths"],
    "dockerfile": ["mode"],
    "linters": ["mode"],
    "sbom": ["mode", "format"],
    "container": ["mode"],
    "dast": ["mode"],
    "sec_func_tests": ["min_automated_percent"],
    "aspm_export": ["mode", "backend"],
    "tooling_pins": ["forbid_image_tags", "manifest"],
    "artifact_registry": ["default_backend", "allowed_backends", "manifest"],
}


def parse_sections(path: Path) -> dict[str, set[str]]:
    sections: dict[str, set[str]] = {}
    current = None
    for line in path.read_text(encoding="utf-8").splitlines():
        top = re.match(r"^([a-z_]+):\s*$", line)
        if top:
            current = top.group(1)
            sections[current] = set()
            continue
        if current and re.match(r"^\s+\w+:", line):
            key = re.match(r"^\s+(\w+):", line)
            if key:
                sections[current].add(key.group(1))
    return sections


def main() -> None:
    policy = Path("config/security-gate-policy.yaml")
    if not policy.exists():
        print(f"Missing {policy}", file=sys.stderr)
        sys.exit(1)

    sections = parse_sections(policy)
    errors = []
    for section, keys in REQUIRED.items():
        if section not in sections:
            errors.append(f"missing section: {section}")
            continue
        for key in keys:
            if key not in sections[section]:
                errors.append(f"{section}: missing key {key}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print("OK: policy schema valid")


if __name__ == "__main__":
    main()
