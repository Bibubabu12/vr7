"""Command line interface entry point."""

import sys

from .apt import AptRepository
from .config import parse_config
from .errors import DepGraphError, RepoError
from .graph import build_graph, format_edges
from .order import format_order, load_order
from .testrepo import GraphFileRepository

EXIT_OK = 0
EXIT_ERROR = 1


def load_repository(config):
    """Открыть реальный индекс apt или файл тестового репозитория."""
    if config.test_mode:
        return GraphFileRepository.from_file(config.repo)
    return AptRepository.from_url(config.repo)


def find_package(repo, name):
    """Возвращает пакет по имени или вызывает ошибку RepoError."""
    package = repo.resolve(name)
    if package is None:
        raise RepoError(f"package not found in repository: {name}")
    return package


def run(config):
    """Строит граф и выводит его ребра или порядок загрузки."""
    repo = load_repository(config)
    root = find_package(repo, config.package)
    graph = build_graph(repo, root, config.max_depth)
    if config.order:
        print("\n".join(format_order(load_order(graph))))
        return
    print("\n".join(format_edges(graph)))


def main(argv=None):
    """Запускает инструмент и возвращает код завершения процесса."""
    try:
        run(parse_config(argv))
    except DepGraphError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK