from __future__ import annotations

import pytest


@pytest.mark.unit
def test_assessment_dag_validation():
    from graph.dag import DirectedAcyclicGraph, assessment_dag

    dag = assessment_dag()
    assert dag.topological_order() == ["ingest", "run_agent", "critic", "hitl_gate", "report"]
    dag.validate_acyclic()

    with pytest.raises(ValueError, match="Unknown DAG node"):
        DirectedAcyclicGraph(nodes=("a",), edges=(("a", "b"),)).topological_order()
    with pytest.raises(ValueError, match="cycle"):
        DirectedAcyclicGraph(nodes=("a", "b"), edges=(("a", "b"), ("b", "a"))).validate_acyclic()
