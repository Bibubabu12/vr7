"""Command line interface entry point."""

import sys

from .apt import AptRepository
from .config import parse_config
from .dot import render_png, to_dot
from .errors import DepGraphError, RepoError
from .graph import build_graph
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
    """Строит граф, выводит порядок загрузки или рисует граф."""
    repo = load_repository(config)
    root = find_package(repo, config.package)
    graph = build_graph(repo, root, config.max_depth)
    if config.order:
        print("\n".join(format_order(load_order(graph))))
        return
    dot_text = to_dot(graph)
    print(dot_text, end="")
    render_png(dot_text, config.output)
    print(f"saved image to {config.output}", file=sys.stderr)


def main(argv=None):
    """Запускает инструмент и возвращает код завершения процесса."""
    try:
        run(parse_config(argv))
    except DepGraphError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK