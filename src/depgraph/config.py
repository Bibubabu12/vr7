"""Параметры командной строки и их валидация."""

import argparse
import os
import re
from dataclasses import dataclass

from .errors import ConfigError

MIN_DEPTH = 0
DEFAULT_DEPTH = 3
DEFAULT_OUTPUT = "graph.png"
IMAGE_SUFFIX = ".png"
APT_NAME = re.compile(r"[a-z0-9][a-z0-9+.\-]*")
TEST_NAME = re.compile(r"[A-Z]+")
URL_PREFIXES = ("http://", "https://", "file://")


@dataclass(frozen=True)
class Config:
    """Проверенные параметры одного запуска."""

    package: str
    repo: str
    test_mode: bool
    output: str
    max_depth: int


class _Parser(argparse.ArgumentParser):
    """Парсер аргументов, сообщающий о проблемах как ConfigError."""

    def error(self, message):
        """Вызывает ConfigError вместо завершения процесса."""
        raise ConfigError(message)


def build_parser():
    """Создает парсер параметров командной строки."""
    parser = _Parser(
        prog="depgraph",
        description="Визуализатор графа зависимостей для apt-пакетов.",
    )
    parser.add_argument(
        "-p", "--package", required=True,
        help="имя анализируемого пакета",
    )
    parser.add_argument(
        "-r", "--repo", required=True,
        help="URL индекса Packages или файл в тестовом режиме",
    )
    parser.add_argument(
        "-t", "--test-mode", action="store_true",
        help="рассматривать --repo как путь к файлу тестового репозитория",
    )
    parser.add_argument(
        "-o", "--output", default=DEFAULT_OUTPUT,
        help="имя сгенерированного PNG-файла (по умолчанию: %(default)s)",
    )
    parser.add_argument(
        "-d", "--max-depth", default=str(DEFAULT_DEPTH),
        help="максимальная глубина зависимостей (по умолчанию: %(default)s)",
    )
    return parser


def check_package(name, test_mode):
    """Проверяет имя пакета на соответствие правилам именования для текущего режима."""
    pattern = TEST_NAME if test_mode else APT_NAME
    if not pattern.fullmatch(name):
        kind = "заглавные латинские буквы" if test_mode else "имя apt"
        raise ConfigError(f"недопустимое имя пакета {name!r}: ожидалось {kind}")


def check_repo(repo, test_mode):
    """Проверяет, что репозиторий является читаемым файлом или известным URL."""
    if test_mode:
        if not os.path.isfile(repo):
            raise ConfigError(f"файл тестового репозитория не найден: {repo}")
    elif not repo.startswith(URL_PREFIXES):
        raise ConfigError(f"репозиторий должен быть http(s) или file URL: {repo}")


def check_output(path):
    """Проверяет, что изображение может быть записано по указанному пути."""
    if not path.lower().endswith(IMAGE_SUFFIX):
        raise ConfigError(f"выходной файл должен заканчиваться на {IMAGE_SUFFIX}")
    folder = os.path.dirname(path) or os.curdir
    if not os.path.isdir(folder):
        raise ConfigError(f"выходная директория не существует: {folder}")


def parse_depth(text):
    """Преобразует опцию глубины в неотрицательное целое число."""
    try:
        value = int(text)
    except ValueError:
        raise ConfigError(f"максимальная глубина должна быть целым числом: {text!r}") from None
    if value < MIN_DEPTH:
        raise ConfigError(f"максимальная глубина должна быть >= {MIN_DEPTH}: {value}")
    return value


def parse_config(argv=None):
    """Разбирает и проверяет параметры командной строки в объект Config."""
    args = build_parser().parse_args(argv)
    check_package(args.package, args.test_mode)
    check_repo(args.repo, args.test_mode)
    check_output(args.output)
    return Config(
        package=args.package,
        repo=args.repo,
        test_mode=args.test_mode,
        output=args.output,
        max_depth=parse_depth(args.max_depth),
    )