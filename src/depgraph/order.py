"""Порядок загрузки: каждый пакет идёт после своих зависимостей."""

from .errors import GraphError


def _visit(graph, name, seen, order):
    """Шаг DFS в post-order; цикл обрывается на уже увиденном пакете."""
    if name in seen:
        return
    seen.add(name)
    for dependency in graph.edges.get(name, []):
        _visit(graph, dependency, seen, order)
    order.append(name)


def load_order(graph):
    """Возвращает пакеты в порядке, в котором их необходимо загружать.

    Зависимости идут перед зависящими от них пакетами, корневой пакет
    оказывается последним. В цикле пакет, достигнутый первым,
    загружается последним.
    """
    order = []
    try:
        _visit(graph, graph.root, set(), order)
    except RecursionError:
        raise GraphError("graph is too deep to compute load order") from None
    return order


def format_order(order):
    """Возвращает пронумерованные строчки текста для порядка загрузки."""
    return [f"{number}. {name}" for number, name in enumerate(order, start=1)]