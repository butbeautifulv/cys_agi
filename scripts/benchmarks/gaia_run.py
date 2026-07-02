#!/usr/bin/env python3
"""GAIA benchmark harness (optional profile — requires HuggingFace dataset access)."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from cys_core.benchmarks.gaia_normalizer import score_gaia


def _load_rows(data_dir: Path, level: int, split: str) -> list[dict]:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise SystemExit("Install pyarrow to read GAIA parquet splits") from exc
    candidates = [
        data_dir / "2023" / split / "metadata.parquet",
        data_dir / f"metadata.level{level}.parquet",
        data_dir / "metadata.parquet",
    ]
    for path in candidates:
        if path.is_file():
            table = pq.read_table(path)
            return table.to_pylist()
    raise FileNotFoundError(f"No GAIA metadata parquet found under {data_dir}")


def _resolve_file_path(data_dir: Path, row: dict) -> str:
    for key in ("file_path", "file_name"):
        rel = row.get(key)
        if not rel:
            continue
        candidate = data_dir / str(rel)
        if candidate.is_file():
            return str(candidate.resolve())
        alt = data_dir / "2023" / "validation" / str(rel)
        if alt.is_file():
            return str(alt.resolve())
    return ""


async def _run_agent_rows(rows: list[dict], data_dir: Path) -> dict[str, str]:
    from bootstrap.container import get_container
    from cys_core.benchmarks.gaia_pipeline import run_gaia_solver

    get_container()
    predictions: dict[str, str] = {}
    for row in rows:
        task_id = str(row.get("task_id", ""))
        question = str(row.get("Question", row.get("question", "")))
        file_path = _resolve_file_path(data_dir, row)
        try:
            out = await run_gaia_solver(question, file_path=file_path)
            predictions[task_id] = str(out.get("prediction", ""))
        except Exception as exc:
            predictions[task_id] = ""
            print(f"agent run failed for {task_id}: {exc}", file=sys.stderr)
    return predictions


def main() -> int:
    parser = argparse.ArgumentParser(description="Run GAIA dev scoring against Egregore gaia_solver profile")
    parser.add_argument("--data-dir", default=os.environ.get("GAIA_DATA_DIR", ""))
    parser.add_argument("--level", type=int, default=1)
    parser.add_argument("--split", default="validation")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--predictions", default="", help="JSONL file with task_id and prediction")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--run-agent", action="store_true", help="Invoke gaia_solver agent end-to-end")
    args = parser.parse_args()

    data_dir = Path(args.data_dir) if args.data_dir else None
    if args.download or data_dir is None:
        try:
            from huggingface_hub import snapshot_download
        except ImportError as exc:
            raise SystemExit("pip install huggingface_hub for --download") from exc
        data_dir = Path(snapshot_download(repo_id="gaia-benchmark/GAIA", repo_type="dataset"))

    rows = _load_rows(data_dir, args.level, args.split)[: args.limit]
    predictions: dict[str, str] = {}
    if args.predictions:
        for line in Path(args.predictions).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            predictions[str(item.get("task_id"))] = str(item.get("prediction", ""))
    elif args.run_agent:
        predictions = asyncio.run(_run_agent_rows(rows, data_dir))

    passed = 0
    results: list[dict] = []
    for row in rows:
        task_id = str(row.get("task_id", ""))
        question = str(row.get("Question", row.get("question", "")))
        reference = str(row.get("Final answer", row.get("final_answer", "")))
        prediction = predictions.get(task_id, "")
        ok = score_gaia(prediction, reference) if prediction and reference else False
        passed += int(ok)
        results.append(
            {
                "task_id": task_id,
                "question": question[:120],
                "passed": ok,
                "reference": reference,
                "prediction": prediction,
            }
        )

    summary = {"total": len(results), "passed": passed, "accuracy": passed / len(results) if results else 0.0}
    print(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2))

    eval_backend_name = os.environ.get("OBS_EVAL_BACKEND", "noop")
    if eval_backend_name == "langfuse":
        try:
            from bootstrap.container import get_container

            backend = get_container().get_eval_backend()
            for item in results:
                backend.record_score(item["task_id"], "gaia_exact_match", 1.0 if item["passed"] else 0.0)
        except Exception as exc:
            print(f"Langfuse eval recording skipped: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
