"""Тесты построения графа и тестового репозитория."""

import contextlib
import io
import unittest
from pathlib import Path

from depgraph.cli import EXIT_ERROR, EXIT_OK, main
from depgraph.errors import GraphError, RepoError
from depgraph.graph import build_graph, format_edges
from depgraph.testrepo import GraphFileRepository, parse_graph_text

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
UNLIMITED = 100


def repo_from(text):
    """Строит тестовый репозиторий из текста описания."""
    return GraphFileRepository(parse_graph_text(text))


class ParseTest(unittest.TestCase):
    """Разбор формата тестового репозитория."""

    def test_parse(self):
        """Комментарии, пустые строки и конечные пакеты обрабатываются корректно."""
        graph = parse_graph_text("A: B C  # note\n\nB:\n")
        self.assertEqual(graph, {"A": ["B", "C"], "B": [], "C": []})

    def test_bad_lines(self):
        """Некорректные строки вызывают RepoError."""
        for text in ("a: B", "A B", "A: b", ": B"):
            with self.subTest(text=text):
                with self.assertRaises(RepoError):
                    parse_graph_text(text)

    def test_missing_file(self):
        """Отсутствующий файл вызывает RepoError."""
        with self.assertRaises(RepoError):
            GraphFileRepository.from_file("no_such_file.txt")


class BuildTest(unittest.TestCase):
    """Поведение рекурсивного обхода в глубину (DFS)."""

    def test_chain_depth_limit(self):
        """Пакеты глубже предельного значения не раскрываются."""
        repo = GraphFileRepository.from_file(EXAMPLES / "chain.txt")
        graph = build_graph(repo, "A", 2)
        self.assertEqual(graph.nodes(), ["A", "B", "C"])
        self.assertEqual(graph.edges["C"], [])

    def test_zero_depth(self):
        """Глубина ноль содержит только корневой узел."""
        repo = repo_from("A: B")
        self.assertEqual(build_graph(repo, "A", 0).nodes(), ["A"])

    def test_diamond_has_no_duplicates(self):
        """Общая зависимость появляется ровно один раз."""
        repo = GraphFileRepository.from_file(EXAMPLES / "diamond.txt")
        graph = build_graph(repo, "A", UNLIMITED)
        self.assertEqual(graph.nodes(), ["A", "B", "D", "C"])
        self.assertEqual(graph.edges["C"], ["D"])

    def test_cycle(self):
        """Циклы завершают обход, а замыкающие ребра фиксируются."""
        repo = GraphFileRepository.from_file(EXAMPLES / "cycle.txt")
        graph = build_graph(repo, "A", UNLIMITED)
        self.assertEqual(graph.nodes(), ["A", "B", "C"])
        self.assertEqual(graph.cycles, [("C", "A"), ("C", "B")])

    def test_self_dependency(self):
        """Пакет, зависящий сам от себя, представляет собой цикл из одного узла."""
        graph = build_graph(repo_from("A: A"), "A", UNLIMITED)
        self.assertEqual(graph.cycles, [("A", "A")])

    def test_shorter_path_expands_again(self):
        """Узел, изначально встреченный слишком глубоко, раскрывается по более короткому пути."""
        repo = GraphFileRepository.from_file(EXAMPLES / "shortcut.txt")
        graph = build_graph(repo, "A", 3)
        self.assertIn("F", graph.nodes())
        self.assertEqual(graph.edges["D"], ["F"])

    def test_recursion_limit(self):
        """Слишком глубокие графы вызывают GraphError, а не RecursionError."""
        size = 3000
        names = [f"N{i}" for i in range(size)]
        graph = {n: [m] for n, m in zip(names, names[1:])}
        graph[names[-1]] = []
        repo = GraphFileRepository(graph)
        with self.assertRaises(GraphError):
            build_graph(repo, names[0], size)

    def test_format(self):
        """Ребра и циклы преобразуются в текстовые строки."""
        graph = build_graph(repo_from("A: B\nB: A"), "A", UNLIMITED)
        self.assertEqual(
            format_edges(graph), ["A -> B", "B -> A", "cycle: B -> A"]
        )


class CliTest(unittest.TestCase):
    """Тестовый режим через командную строку."""

    def run_cli(self, *args):
        """Запускает main и возвращает код выхода и строки stdout."""
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(list(args))
        return code, out.getvalue().splitlines()

    def test_test_mode(self):
        """CLI работает с файлом тестового репозитория."""
        path = str(EXAMPLES / "chain.txt")
        args = ("-t", "-p", "A", "-r", path, "-d", "1", "--order")
        code, lines = self.run_cli(*args)
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(lines, ["1. B", "2. A"])

    def test_unknown_package(self):
        """Отсутствующий в тестовом репозитории пакет вызывает ошибку."""
        path = str(EXAMPLES / "chain.txt")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code, _ = self.run_cli("-t", "-p", "Z", "-r", path)
        self.assertEqual(code, EXIT_ERROR)