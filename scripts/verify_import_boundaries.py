from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "cys_core"

# Shrink-only: infrastructure/registry paths pending phase-4 runtime_config migration.
ALLOWLIST = {
    "cys_core/application/use_cases/invoke_tool.py",
    "cys_core/infrastructure/auth/broker.py",
    "cys_core/infrastructure/auth/factory.py",
    "cys_core/infrastructure/bus_transport.py",
    "cys_core/infrastructure/job_store/factory.py",
    "cys_core/infrastructure/k8s_sandbox.py",
    "cys_core/infrastructure/kafka_audit.py",
    "cys_core/infrastructure/kafka_bus.py",
    "cys_core/infrastructure/kafka_bus_events.py",
    "cys_core/infrastructure/kafka_control_events.py",
    "cys_core/infrastructure/kafka_events.py",
    "cys_core/infrastructure/kafka_paused.py",
    "cys_core/infrastructure/kafka_queue.py",
    "cys_core/infrastructure/memory/factory.py",
    "cys_core/infrastructure/queue.py",
    "cys_core/infrastructure/sandbox.py",
    "cys_core/middleware/security_middleware.py",
    "cys_core/observability/platform_gauges.py",
    "cys_core/persistence.py",
    "cys_core/registry/mcp_tools.py",
    "cys_core/registry/product_context.py",
    "cys_core/registry/skills_tool.py",
    "cys_core/registry/veil_tools.py",
    "cys_core/security/rate_limit.py",
}


def _imports_in_file(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def main() -> int:
    violations: list[str] = []
    for path in CORE.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if rel in ALLOWLIST:
            continue
        for mod in _imports_in_file(path):
            if mod.startswith("bootstrap.") or mod.startswith("interfaces."):
                violations.append(f"{rel}: {mod}")
    if violations:
        print("Import boundary violations:")
        for line in sorted(violations):
            print(line)
        return 1
    print("OK: no bootstrap/interfaces imports in cys_core (outside shrink-only allowlist)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
