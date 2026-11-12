"""Построение графа зависимостей рекурсивным обходом в глубину (DFS)."""

from dataclasses import dataclass, field

from .errors import GraphError


@dataclass
class Graph:
    """Направленный граф зависимостей, достижимый из корневого пакета."""

    root: str
    edges: dict = field(default_factory=dict)
    cycles: list = field(default_factory=list)

    def nodes(self):
        """Возвращает все пакеты графа в порядке их обнаружения."""
        return list(self.edges)


class GraphWalker:
    """Рекурсивный DFS с ограничением глубины и учётом кратчайшего пути."""

    def __init__(self, repo, max_depth):
        """Подготавливает пустое состояние обхода."""
        self.repo = repo
        self.max_depth = max_depth
        self.depth = {}
        self.path = set()
        self.graph = None

    def link(self, name, dependency):
        """Записывает ребро и сохраняет его, если оно замыкает цикл."""
        edges = self.graph.edges[name]
        if dependency not in edges:
            edges.append(dependency)
        pair = (name, dependency)
        if dependency in self.path and pair not in self.graph.cycles:
            self.graph.cycles.append(pair)

    def visit(self, name, level):
        """Посещает пакет; повторно — только по более короткому пути."""
        known = self.depth.get(name)
        if known is not None and known <= level:
            return
        self.depth[name] = level
        self.graph.edges.setdefault(name, [])
        if level >= self.max_depth:
            return
        self.path.add(name)
        for dependency in self.repo.dependencies(name):
            self.link(name, dependency)
            self.visit(dependency, level + 1)
        self.path.discard(name)


def build_graph(repo, root, max_depth):
    """Строит граф зависимостей для root глубиной не более max_depth уровней.

    Пакеты на пределе глубины включаются в граф, но не раскрываются. Циклы
    останавливают обход и перечисляются в ``Graph.cycles``.
    """
    walker = GraphWalker(repo, max_depth)
    walker.graph = Graph(root)
    try:
        walker.visit(root, 0)
    except RecursionError:
        raise GraphError(
            f"max depth {max_depth} is too large for recursive DFS"
        ) from None
    return walker.graph


def format_edges(graph):
    """Возвращает строки с ребрами, изолированными узлами и циклами."""
    lines = []
    for name, dependencies in graph.edges.items():
        if dependencies:
            lines += [f"{name} -> {dep}" for dep in dependencies]
        else:
            lines.append(name)
    lines += [f"cycle: {a} -> {b}" for a, b in graph.cycles]
    return lines