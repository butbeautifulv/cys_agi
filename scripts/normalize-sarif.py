#!/usr/bin/env python3
"""Ensure SARIF is valid for GitHub upload-sarif and gate-check.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SARIF_VERSION = "2.1.0"
DEFAULT_LOCATION = {
    "physicalLocation": {
        "artifactLocation": {"uri": "unknown", "uriBaseId": "%SRCROOT%"},
        "region": {"startLine": 1},
    }
}


def normalize(path: str, tool_name: str = "scanner") -> None:
    report = Path(path)
    report.parent.mkdir(parents=True, exist_ok=True)

    data: dict
    if report.exists() and report.stat().st_size > 0:
        try:
            loaded = json.loads(report.read_text(encoding="utf-8"))
            data = loaded if isinstance(loaded, dict) else {}
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}

    data.setdefault("version", SARIF_VERSION)
    runs = data.get("runs")
    if not isinstance(runs, list) or not runs:
        runs = [{}]
        data["runs"] = runs

    for run in runs:
        if not isinstance(run, dict):
            continue
        tool = run.setdefault("tool", {})
        if not isinstance(tool, dict):
            tool = {}
            run["tool"] = tool
        driver = tool.setdefault("driver", {})
        if not isinstance(driver, dict):
            driver = {}
            tool["driver"] = driver
        driver.setdefault("name", tool_name)

        results = run.get("results")
        if results is None:
            run["results"] = []
            continue
        if not isinstance(results, list):
            run["results"] = []
            continue

        for result in results:
            if not isinstance(result, dict):
                continue
            locations = result.get("locations")
            if not locations:
                result["locations"] = [json.loads(json.dumps(DEFAULT_LOCATION))]
                continue
            if isinstance(locations, list):
                for location in locations:
                    if isinstance(location, dict) and "physicalLocation" not in location:
                        location["physicalLocation"] = json.loads(
                            json.dumps(DEFAULT_LOCATION["physicalLocation"])
                        )

    report.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: normalize-sarif.py REPORT [TOOL_NAME]", file=sys.stderr)
        return 2
    tool = sys.argv[2] if len(sys.argv) > 2 else "scanner"
    normalize(sys.argv[1], tool)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
