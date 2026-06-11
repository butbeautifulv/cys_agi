from __future__ import annotations

import json
import runpy
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


@pytest.mark.unit
def test_main_cli_commands_and_entrypoint(monkeypatch, capsys):
    import coordinator.deep_assessment as deep_assessment
    import graph.workflow as workflow
    import main

    monkeypatch.setattr(workflow, "run_assessment", lambda *args, **kwargs: {"__interrupt__": "approval"})
    assert main.cmd_assess(SimpleNamespace(input="raw", thread_id="tid")) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "pending_approval"

    monkeypatch.setattr(workflow, "run_assessment", lambda *args, **kwargs: {"report": {"status": "ok"}})
    assert main.cmd_assess(SimpleNamespace(input="raw", thread_id="tid")) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "ok"

    monkeypatch.setattr(
        deep_assessment,
        "run_session",
        lambda *args, **kwargs: {"messages": [SimpleNamespace(content={"answer": "ok"})]},
    )
    assert main.cmd_session(SimpleNamespace(goal="goal", thread_id="sid")) == 0
    assert json.loads(capsys.readouterr().out)["answer"] == "ok"

    monkeypatch.setattr(deep_assessment, "run_session", lambda *args, **kwargs: {"status": "empty"})
    assert main.cmd_session(SimpleNamespace(goal="goal", thread_id="sid")) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "empty"

    registry = SimpleNamespace(
        names=lambda: ["alpha"],
        get=lambda name: SimpleNamespace(name="alpha", role="specialist", sample_input="sample"),
    )
    runtime = SimpleNamespace(run=lambda name, user_input, session_id: {"name": name, "input": user_input, "sid": session_id})
    monkeypatch.setattr(main, "get_agent_registry", lambda: registry)
    monkeypatch.setattr(main, "get_runtime", lambda: runtime)
    assert main.cmd_agent(SimpleNamespace(name="missing", input=None)) == 1
    assert "Unknown agent" in capsys.readouterr().err
    assert main.cmd_agent(SimpleNamespace(name="alpha", input=None)) == 0
    assert json.loads(capsys.readouterr().out)["input"] == "sample"
    assert main.cmd_agent(SimpleNamespace(name="alpha", input="explicit")) == 0
    assert json.loads(capsys.readouterr().out)["input"] == "explicit"

    monkeypatch.setattr(workflow, "run_assessment", lambda *args, **kwargs: {"report": {"approved": kwargs["resume"]}})
    assert main.cmd_resume(SimpleNamespace(thread_id="tid", approve=True)) == 0
    assert json.loads(capsys.readouterr().out)["approved"] is True
    assert main.cmd_resume(SimpleNamespace(thread_id="tid", approve=False)) == 0
    assert json.loads(capsys.readouterr().out)["approved"] == {"approved": False}

    pytest_main = MagicMock(return_value=5)
    monkeypatch.setattr(pytest, "main", pytest_main)
    assert main.cmd_adversarial_test(SimpleNamespace()) == 5
    pytest_main.assert_called_with(["-q", "tests"])

    assert main.cmd_info(SimpleNamespace()) == 0
    info = json.loads(capsys.readouterr().out)
    assert info["project"] == "cys-agi"
    assert info["agents"] == ["alpha"]

    parser = main.build_parser()
    assert parser.parse_args(["agent", "alpha"]).name == "alpha"

    monkeypatch.setattr(main, "build_parser", lambda: SimpleNamespace(parse_args=lambda: SimpleNamespace(func=lambda args: 7)))
    with pytest.raises(SystemExit) as exit_info:
        main.main()
    assert exit_info.value.code == 7


@pytest.mark.unit
def test_main_module_entrypoint_info(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["main.py", "info"])
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module("main", run_name="__main__")
    assert exit_info.value.code == 0
    assert json.loads(capsys.readouterr().out)["project"] == "cys-agi"
