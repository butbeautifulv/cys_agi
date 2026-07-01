from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "cys_core"


def _rg(pattern: str, path: Path) -> list[str]:
    result = subprocess.run(
        ["rg", "-n", pattern, str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 1:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


@pytest.mark.unit
def test_registry_agents_no_bootstrap_product_loader():
    matches = _rg(r"from bootstrap\.product_loader", CORE / "registry")
    assert matches == []


@pytest.mark.unit
def test_infrastructure_no_interfaces_imports():
    matches = _rg(r"from interfaces\.|import interfaces\.", CORE / "infrastructure")
    assert matches == []


@pytest.mark.unit
def test_verify_no_langfuse_in_core_script():
    script = ROOT / "scripts" / "verify_no_langfuse_in_core.sh"
    result = subprocess.run(["bash", str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.unit
def test_verify_import_boundaries_script():
    script = ROOT / "scripts" / "verify_import_boundaries.py"
    result = subprocess.run(["uv", "run", "python", str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
