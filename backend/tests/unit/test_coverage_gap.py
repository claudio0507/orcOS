import pytest
from decimal import Decimal
from app.pricing_engine.bom_dag import BomGraph
from app.pricing_engine.spreading import spread_fixed_costs, SpreadingLine
from app.pricing_engine.rounding import round_money

def test_bom_dag_has_cycle_direct():
    """Cobre has_cycle com um ciclo direto."""
    g = BomGraph()
    # A -> B -> A
    g.add_node("A")
    g.add_node("B")
    g._adj["A"].add("B")
    g._adj["B"].add("A")
    
    assert g.has_cycle() is True

def test_bom_dag_has_cycle_nested():
    """Cobre branches recursivas do has_cycle."""
    g = BomGraph()
    # A -> B -> C -> B (Ciclo em B-C)
    g.add_node("A")
    g.add_node("B")
    g.add_node("C")
    g._adj["A"].add("B")
    g._adj["B"].add("C")
    g._adj["C"].add("B")
    
    assert g.has_cycle() is True

def test_bom_dag_find_path_start_is_target():
    """Cobre start == target no _find_path."""
    g = BomGraph()
    g.add_node("X")
    assert g._find_path("X", "X") == ["X"]

def test_bom_dag_find_path_already_visited_non_target():
    """Cobre a branch nxt in visited para nó não-target no _find_path."""
    g = BomGraph()
    # Grafo:
    # A -> B -> C
    # A -> D -> C
    # Target = UNREACHABLE
    g.add_edge("A", "B")
    g.add_edge("B", "C")
    g.add_edge("A", "D")
    g.add_edge("D", "C")
    
    # Busca A -> "NON_EXISTENT". Obrigatoriamente passará por C duas vezes.
    assert g._find_path("A", "NON_EXISTENT") is None

def test_rounding_invalid_mode():
    """Cobre o raise de erro para modo de arredondamento desconhecido."""
    # Como _DECIMAL_RULE é um dict, acessar com chave inexistente dá KeyError.
    with pytest.raises(KeyError):
        round_money(Decimal("10.5"), mode="invalid")

def test_spreading_fixed_cost_zero():
    """Edge case: custo fixo zero."""
    lines = [SpreadingLine("L1", Decimal("100"), Decimal("2"))]
    result = spread_fixed_costs(lines=lines, fixed_total=Decimal("0"))
    assert result[0].allocated_fixed == 0

def test_spreading_total_weight_zero_and_fixed_zero():
    """Edge case: tudo zero."""
    lines = [SpreadingLine("L1", Decimal("0"), Decimal("1"))]
    result = spread_fixed_costs(lines=lines, fixed_total=Decimal("0"))
    assert result[0].final_unit_price == 0
