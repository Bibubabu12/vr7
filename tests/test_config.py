"""Тесты синтаксического анализа и валидации параметров командной строки."""

import contextlib
import io
import os
import tempfile
import unittest

from depgraph.cli import EXIT_ERROR, main
from depgraph.config import parse_config
from depgraph.errors import ConfigError

URL = "https://archive.ubuntu.com/ubuntu/Packages.gz"


class ConfigTest(unittest.TestCase):
    """Проверка каждого предоставленного пользователем параметра."""

    def test_valid_real_mode(self):
        """Валидные опции дают Config со значениями по умолчанию."""
        config = parse_config(["-p", "curl", "-r", URL])
        self.assertEqual(config.package, "curl")
        self.assertEqual(config.max_depth, 3)
        self.assertEqual(config.output, "graph.png")
        self.assertFalse(config.test_mode)

    def test_valid_test_mode(self):
        """Тестовый режим принимает существующий файл и заглавные буквы."""
        with tempfile.NamedTemporaryFile(suffix=".txt") as repo:
            argv = ["-t", "-p", "A", "-r", repo.name, "-d", "5"]
            config = parse_config(argv)
        self.assertTrue(config.test_mode)
        self.assertEqual(config.max_depth, 5)

    def test_missing_required(self):
        """Отсутствие пакета или репозитория приводит к ошибке."""
        with self.assertRaises(ConfigError):
            parse_config(["-r", URL])
        with self.assertRaises(ConfigError):
            parse_config(["-p", "curl"])

    def test_invalid_package(self):
        """Имена, не соответствующие правилам именования apt, отклоняются."""
        with self.assertRaises(ConfigError):
            parse_config(["-p", "Bad Name", "-r", URL])
        with self.assertRaises(ConfigError):
            parse_config(["-t", "-p", "a", "-r", __file__])

    def test_invalid_repo(self):
        """Репозиторий: URL или существующий файл в тестовом режиме."""
        with self.assertRaises(ConfigError):
            parse_config(["-p", "curl", "-r", "ftp://example.org"])
        with self.assertRaises(ConfigError):
            parse_config(["-t", "-p", "A", "-r", "missing.txt"])

    def test_invalid_depth(self):
        """Глубина должна быть неотрицательным целым числом."""
        for value in ("-1", "abc", "1.5"):
            with self.subTest(value=value):
                with self.assertRaises(ConfigError):
                    parse_config(["-p", "curl", "-r", URL, "-d", value])

    def test_invalid_output(self):
        """Выходным файлом должен быть PNG-файл в существующей директории."""
        with self.assertRaises(ConfigError):
            parse_config(["-p", "curl", "-r", URL, "-o", "graph.txt"])
        missing = os.path.join("no_such_dir", "graph.png")
        with self.assertRaises(ConfigError):
            parse_config(["-p", "curl", "-r", URL, "-o", missing])


class CliTest(unittest.TestCase):
    """Поведение точки входа."""

    def test_error_exit_code(self):
        """Неверные параметры выводят сообщение и ненулевой код выхода."""
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = main(["-p", "curl", "-r", URL, "-d", "-3"])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("error:", err.getvalue())