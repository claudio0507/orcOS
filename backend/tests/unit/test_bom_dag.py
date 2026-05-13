"""Unit tests for bom_dag.py — cycle detection in component graphs."""
from __future__ import annotations

import pytest

from app.pricing_engine.bom_dag import BomGraph
from app.pricing_engine.exceptions import CycleError


def test_empty_graph():
    """Empty graph has no cycle."""
    dag = BomGraph()
    assert dag.has_cycle() is False
    assert dag.nodes() == frozenset()


def test_single_node_no_cycle():
    """Single node graph has no cycle."""
    dag = BomGraph()
    dag.add_node("A")
    assert dag.has_cycle() is False
    assert dag.nodes() == frozenset({"A"})


def test_add_node_idempotent():
    """Adding same node twice is idempotent."""
    dag = BomGraph()
    dag.add_node("A")
    dag.add_node("A")
    assert dag.nodes() == frozenset({"A"})


def test_linear_chain_no_cycle():
    """Linear chain A→B→C has no cycle."""
    dag = BomGraph()
    dag.add_edge("A", "B")
    dag.add_edge("B", "C")
    assert dag.has_cycle() is False
    assert dag.children("A") == frozenset({"B"})
    assert dag.children("B") == frozenset({"C"})
    assert dag.children("C") == frozenset()


def test_self_loop_raises_cycle_error():
    """Self-edge A→A raises CycleError immediately."""
    dag = BomGraph()
    with pytest.raises(CycleError) as exc_info:
        dag.add_edge("A", "A")
    assert exc_info.value.path == ["A", "A"]


def test_two_node_cycle_raises():
    """Cycle A→B→A raises CycleError on second edge."""
    dag = BomGraph()
    dag.add_edge("A", "B")
    with pytest.raises(CycleError) as exc_info:
        dag.add_edge("B", "A")
    assert "A" in exc_info.value.path
    assert "B" in exc_info.value.path


def test_three_node_cycle_raises():
    """Cycle A→B→C→A raises on closing edge."""
    dag = BomGraph()
    dag.add_edge("A", "B")
    dag.add_edge("B", "C")
    with pytest.raises(CycleError):
        dag.add_edge("C", "A")
    # Graph remains consistent; edge not added
    assert dag.children("C") == frozenset()


def test_diamond_dag_no_cycle():
    """Diamond A→{B,C}→D has no cycle."""
    dag = BomGraph()
    dag.add_edge("A", "B")
    dag.add_edge("A", "C")
    dag.add_edge("B", "D")
    dag.add_edge("C", "D")
    assert dag.has_cycle() is False
    assert dag.children("A") == frozenset({"B", "C"})
    assert dag.children("D") == frozenset()


def test_add_edges_multiple():
    """add_edges() adds multiple edges from one parent."""
    dag = BomGraph()
    dag.add_edges("A", ["B", "C", "D"])
    assert dag.children("A") == frozenset({"B", "C", "D"})


def test_add_edge_idempotent():
    """Adding same edge twice is safe."""
    dag = BomGraph()
    dag.add_edge("A", "B")
    dag.add_edge("A", "B")
    assert dag.children("A") == frozenset({"B"})


def test_hashable_node_ids():
    """Node IDs can be any hashable type (strings, UUIDs, ints)."""
    dag = BomGraph()
    dag.add_edge(1, 2)
    dag.add_edge("uuid-A", "uuid-B")
    dag.add_edge(("tuple", "node"), "child")
    assert dag.has_cycle() is False


def test_complex_dag_no_false_positive():
    """Complex DAG with multiple paths does not falsely detect cycle."""
    dag = BomGraph()
    #     A
    #    /|\
    #   B C D
    #   |/  |
    #   E   F
    dag.add_edge("A", "B")
    dag.add_edge("A", "C")
    dag.add_edge("A", "D")
    dag.add_edge("B", "E")
    dag.add_edge("C", "E")
    dag.add_edge("D", "F")
    assert dag.has_cycle() is False
