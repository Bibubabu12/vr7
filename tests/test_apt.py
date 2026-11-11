"""Тесты читчика индекса apt."""

import contextlib
import gzip
import io
import lzma
import unittest
from pathlib import Path

from depgraph import apt
from depgraph.apt import AptRepository
from depgraph.cli import EXIT_ERROR, EXIT_OK, main
from depgraph.errors import RepoError

SAMPLE = Path(__file__).parent / "data" / "Packages.sample"


def load_sample():
    """Возвращает репозиторий, построенный из выборочного индекса."""
    return AptRepository.from_url(SAMPLE.as_uri())


class ParsingTest(unittest.TestCase):
    """Разбор полей зависимостей."""

    def test_clean_name(self):
        """Версии, архитектуры и профили удаляются."""
        self.assertEqual(apt.clean_name("libc6 (>= 2.34)"), "libc6")
        self.assertEqual(apt.clean_name("zlib1g:any"), "zlib1g")
        self.assertEqual(apt.clean_name("x [amd64] <!nocheck>"), "x")

    def test_alternatives(self):
        """Альтернативы группируются, группы разделяются запятыми."""
        groups = apt.parse_dependency_field("a (>= 1), b | c ,")
        self.assertEqual(groups, [["a"], ["b", "c"]])

    def test_continuation_lines(self):
        """Перенесенные строки объединяются с предыдущим полем."""
        fields = apt.parse_stanza("Package: p\nDepends: a,\n b\n")
        self.assertEqual(fields["Depends"], "a, b")

    def test_decompress(self):
        """Обычные данные, gzip и xz успешно декодируются."""
        data = "Package: p\n".encode()
        for packed in (data, gzip.compress(data), lzma.compress(data)):
            self.assertEqual(apt.decompress(packed), "Package: p\n")

    def test_broken_archive(self):
        """Поврежденные сжатые данные вызывают RepoError."""
        with self.assertRaises(RepoError):
            apt.decompress(apt.GZIP_MAGIC + b"garbage")


class RepositoryTest(unittest.TestCase):
    """Зависимости, взятые из выборочного индекса."""

    def test_direct_dependencies(self):
        """Альтернативы, виртуальные пакеты и Pre-Depends работают."""
        repo = load_sample()
        self.assertEqual(
            repo.dependencies("app"),
            ["base-files", "libc6", "libssl3", "mawk", "zlib1g",
             "missing-pkg"],
        )

    def test_virtual_package(self):
        """Виртуальное имя разрешается в своего поставщика."""
        self.assertEqual(load_sample().resolve("awk"), "mawk")

    def test_unknown_package(self):
        """Неизвестные пакеты не разрешаются и не имеют зависимостей."""
        repo = load_sample()
        self.assertIsNone(repo.resolve("nothing"))
        self.assertEqual(repo.dependencies("nothing"), [])

    def test_bad_url(self):
        """Проблемы со скачиванием сообщаются как RepoError."""
        with self.assertRaises(RepoError):
            AptRepository.from_url("file:///no/such/Packages")

    def test_cli_real_mode(self):
        """CLI выводит прямые зависимости пакета из индекса apt."""
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["-p", "app", "-r", SAMPLE.as_uri()])
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(
            out.getvalue().splitlines(),
            ["base-files", "libc6", "libssl3", "mawk", "zlib1g",
             "missing-pkg"],
        )

    def test_cli_unknown_package(self):
        """Неизвестный корневой пакет вызывает ошибку."""
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = main(["-p", "nothing", "-r", SAMPLE.as_uri()])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("not found", err.getvalue())