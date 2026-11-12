"""Тесты вывода Graphviz."""

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

from depgraph.cli import EXIT_ERROR, EXIT_OK, main
from depgraph.dot import quote, render_png, to_dot
from depgraph.errors import RenderError
from depgraph.graph import build_graph
from depgraph.testrepo import GraphFileRepository

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
PNG_MAGIC = b"\x89PNG"
HAS_DOT = shutil.which("dot") is not None
UNLIMITED = 100


def graph_of(name, depth=UNLIMITED):
    """Возвращает граф примерного тестового репозитория с корнем в A."""
    repo = GraphFileRepository.from_file(EXAMPLES / f"{name}.txt")
    return build_graph(repo, "A", depth)


class DotTextTest(unittest.TestCase):
    """Текстовое представление графа."""

    def test_quote(self):
        """Кавычки и обратные слэши экранируются."""
        self.assertEqual(quote('a"b\\c'), '"a\\"b\\\\c"')

    def test_structure(self):
        """Корневой узел выделен, а каждое ребро перечислено."""
        text = to_dot(graph_of("diamond"))
        self.assertTrue(text.startswith("digraph dependencies {"))
        self.assertIn('"A" [shape=box', text)
        for edge in ('"A" -> "B"', '"A" -> "C"', '"B" -> "D"', '"C" -> "D"'):
            self.assertIn(edge, text)

    def test_cycle_edges_are_red(self):
        """Ребра, замыкающие цикл, получают особый цвет."""
        text = to_dot(graph_of("cycle"))
        self.assertIn('"C" -> "A" [color=red', text)
        self.assertNotIn('"A" -> "B" [', text)

    def test_isolated_root(self):
        """Граф из одного корня — всё ещё валидный DOT."""
        text = to_dot(graph_of("chain", depth=0))
        self.assertEqual(text.count("->"), 0)
        self.assertTrue(text.rstrip().endswith("}"))


@unittest.skipUnless(HAS_DOT, "Graphviz не установлен")
class RenderTest(unittest.TestCase):
    """Рендеринг с помощью настоящего Graphviz."""

    def test_render_png(self):
        """Создается PNG-файл."""
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "graph.png")
            render_png(to_dot(graph_of("diamond")), path)
            self.assertTrue(Path(path).read_bytes().startswith(PNG_MAGIC))

    def test_bad_dot(self):
        """Неверный текст DOT вызывает RenderError."""
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(RenderError):
                render_png("not a graph", str(Path(folder) / "x.png"))

    def test_cli_draws_graph(self):
        """CLI выводит текст DOT и записывает изображение."""
        with tempfile.TemporaryDirectory() as folder:
            image = str(Path(folder) / "out.png")
            args = ["-t", "-p", "A", "-d", "5", "-o", image,
                    "-r", str(EXAMPLES / "cycle.txt")]
            out = io.StringIO()
            with contextlib.redirect_stdout(out), \
                    contextlib.redirect_stderr(io.StringIO()):
                code = main(args)
            self.assertEqual(code, EXIT_OK)
            self.assertIn("digraph", out.getvalue())
            self.assertTrue(Path(image).exists())


class MissingToolTest(unittest.TestCase):
    """Поведение при отсутствии Graphviz."""

    def test_missing_dot(self):
        """Отсутствующий исполняемый файл выдает понятную ошибку."""
        from depgraph import dot
        saved = dot.DOT_COMMAND
        dot.DOT_COMMAND = "no-such-graphviz-tool"
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err), \
                    contextlib.redirect_stdout(io.StringIO()):
                code = main(["-t", "-p", "A", "-r",
                             str(EXAMPLES / "chain.txt")])
        finally:
            dot.DOT_COMMAND = saved
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("Graphviz", err.getvalue())