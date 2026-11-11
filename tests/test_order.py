"""Тесты порядка загрузки."""

import contextlib
import io
import unittest
from pathlib import Path

from depgraph.cli import EXIT_OK, main
from depgraph.graph import build_graph
from depgraph.order import format_order, load_order
from depgraph.testrepo import GraphFileRepository, parse_graph_text

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
UNLIMITED = 100


def order_of(name, root="A", depth=UNLIMITED):
    """Возвращает порядок загрузки для примерного тестового репозитория."""
    repo = GraphFileRepository.from_file(EXAMPLES / f"{name}.txt")
    return load_order(build_graph(repo, root, depth))


class OrderTest(unittest.TestCase):
    """Зависимости должны загружаться перед зависящими от них пакетами."""

    def test_chain(self):
        """Цепочка загружается начиная с самого глубокого пакета."""
        self.assertEqual(order_of("chain"), ["D", "C", "B", "A"])

    def test_diamond(self):
        """Общая зависимость загружается один раз, перед обеими зависимыми сторонами."""
        self.assertEqual(order_of("diamond"), ["D", "B", "C", "A"])

    def test_cycle_terminates(self):
        """Каждый пакет из цикла перечисляется ровно один раз."""
        self.assertEqual(order_of("cycle"), ["C", "B", "A"])

    def test_depth_limit(self):
        """Перечисляются только пакеты, попадающие в ограничение глубины."""
        self.assertEqual(order_of("chain", depth=1), ["B", "A"])

    def test_large_graph_is_topological(self):
        """В графе без циклов каждое ребро направлено вперед."""
        text = (EXAMPLES / "large.txt").read_text(encoding="utf-8")
        acyclic = text.replace("M: A", "M:")
        repo = GraphFileRepository(parse_graph_text(acyclic))
        graph = build_graph(repo, "A", UNLIMITED)
        position = {n: i for i, n in enumerate(load_order(graph))}
        for name, dependencies in graph.edges.items():
            for dependency in dependencies:
                self.assertLess(position[dependency], position[name])

    def test_format(self):
        """Строки нумеруются с единицы."""
        self.assertEqual(format_order(["B", "A"]), ["1. B", "2. A"])

    def test_cli_order(self):
        """Опция --order выводит порядок загрузки."""
        out = io.StringIO()
        path = str(EXAMPLES / "diamond.txt")
        with contextlib.redirect_stdout(out):
            code = main(["-t", "-p", "A", "-r", path, "--order"])
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out.getvalue().splitlines()[-1], "4. A")