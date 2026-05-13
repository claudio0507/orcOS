"""
Detecção de ciclos no Bill of Materials — PRD v2.0 §3.5.6.

A cada gravação de `bom_items` o sistema executa DFS no grafo de componentes.
Se a aresta sendo gravada faz com que `child` atinja `parent` transitivamente,
a gravação é rejeitada com o path do ciclo (`CycleError.path`).

O grafo é unidirecional: componente_pai → componente_filho (filho compõe pai).
Materiais "folha" (sem filhos) também podem ser representados, mas não
participam de detecção (não têm arestas saindo).
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable

from app.pricing_engine.exceptions import CycleError


class BomGraph:
    """Grafo dirigido de componentes (single-tenant; o caller é responsável
    pelo isolamento entre tenants).

    Nós são identificadores hashable (em produção, UUIDs de `bom_components`).
    Arestas: parent → child  (filho é insumo do pai).
    """

    def __init__(self) -> None:
        self._adj: dict[Hashable, set[Hashable]] = {}

    # ------------------------------------------------------------------
    # Construção
    # ------------------------------------------------------------------

    def add_node(self, node: Hashable) -> None:
        """
        Garante a existência do nó no grafo.

        Args:
            node: Identificador do componente.
        """
        self._adj.setdefault(node, set())

    def add_edge(self, parent: Hashable, child: Hashable) -> None:
        """
        Adiciona uma aresta direcionada entre pai e filho, representando dependência.

        Verifica se a inclusão da aresta criaria um ciclo no grafo.

        Args:
            parent: Identificador do componente pai.
            child: Identificador do componente filho (insumo).

        Raises:
            CycleError: Se a aresta criar um ciclo de dependência.
        """
        if parent == child:
            raise CycleError(path=[str(parent), str(child)])

        self.add_node(parent)
        self.add_node(child)

        if child in self._adj[parent]:
            return  # aresta já existente; nada a fazer.

        # Se já existe path de child → parent, a nova aresta forma ciclo.
        existing_path = self._find_path(child, parent)
        if existing_path is not None:
            cycle = [str(parent)] + [str(n) for n in existing_path]
            raise CycleError(path=cycle)

        self._adj[parent].add(child)

    def add_edges(self, parent: Hashable, children: Iterable[Hashable]) -> None:
        """
        Adiciona múltiplas arestas a partir de um mesmo nó pai.

        Args:
            parent: Identificador do componente pai.
            children: Iterável de identificadores de componentes filhos.
        """
        for child in children:
            self.add_edge(parent, child)

    # ------------------------------------------------------------------
    # Consulta
    # ------------------------------------------------------------------

    def children(self, node: Hashable) -> frozenset[Hashable]:
        return frozenset(self._adj.get(node, set()))

    def nodes(self) -> frozenset[Hashable]:
        return frozenset(self._adj)

    def has_cycle(self) -> bool:
        """
        Verifica se o grafo inteiro contém algum ciclo.

        Utiliza algoritmo de busca em profundidade (DFS) com coloração de nós.

        Returns:
            True se houver ciclo, False caso contrário.
        """
        white, gray, black = 0, 1, 2
        color: dict[Hashable, int] = dict.fromkeys(self._adj, white)

        def visit(node: Hashable) -> bool:
            color[node] = gray
            for nxt in self._adj.get(node, ()):
                if color.get(nxt, white) == gray:
                    return True
                if color.get(nxt, white) == white and visit(nxt):
                    return True
            color[node] = black
            return False

        return any(color[n] == white and visit(n) for n in self._adj)

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _find_path(self, start: Hashable, target: Hashable) -> list[Hashable] | None:
        """Retorna um path start→...→target (inclusive) ou None se inalcançável."""
        if start == target:
            return [start]
        visited: set[Hashable] = {start}
        # Stack mantém (node, path_to_node_inclusive)
        stack: list[tuple[Hashable, list[Hashable]]] = [(start, [start])]
        while stack:
            node, path = stack.pop()
            for nxt in self._adj.get(node, ()):
                if nxt == target:
                    return [*path, nxt]
                if nxt not in visited:
                    visited.add(nxt)
                    stack.append((nxt, [*path, nxt]))
        return None
