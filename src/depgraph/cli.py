"""Command line interface entry point."""

import sys
from dataclasses import asdict

from .config import parse_config
from .errors import DepGraphError

EXIT_OK = 0
EXIT_ERROR = 1


def format_config(config):
    """Возвращает параметры запуска в виде строк ``ключ=значение``."""
    return [f"{key}={value}" for key, value in asdict(config).items()]


def main(argv=None):
    """Запускает инструмент и возвращает код завершения процесса."""
    try:
        config = parse_config(argv)
    except DepGraphError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    print("\n".join(format_config(config)))
    return EXIT_OK