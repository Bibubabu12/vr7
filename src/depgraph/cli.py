"""Command line interface entry point."""

import sys

from .apt import AptRepository
from .config import parse_config
from .errors import DepGraphError, RepoError

EXIT_OK = 0
EXIT_ERROR = 1


def load_repository(config):
    """Открыть реальный индекс apt."""
    if config.test_mode:
        raise RepoError("тестовый режим пока не поддерживается")
    return AptRepository.from_url(config.repo)


def find_package(repo, name):
    """Возвращает пакет по имени или вызывает ошибку RepoError."""
    package = repo.resolve(name)
    if package is None:
        raise RepoError(f"package not found in repository: {name}")
    return package


def run(config):
    """Выводит прямые зависимости заданного пакета."""
    repo = load_repository(config)
    root = find_package(repo, config.package)
    for dependency in repo.dependencies(root):
        print(dependency)


def main(argv=None):
    """Запускает инструмент и возвращает код завершения процесса."""
    try:
        run(parse_config(argv))
    except DepGraphError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK