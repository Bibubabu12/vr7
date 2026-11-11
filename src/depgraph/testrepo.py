"""Тестовый репозиторий: текстовый файл, описывающий граф пакетов.

Каждая строка имеет формат ``A: B C``, что означает зависимость пакета A от B
и C. Имена пакетов — заглавные латинские буквы. Текст после ``#``
игнорируется, пустые строки пропускаются.
"""

import re
from pathlib import Path

from .errors import RepoError

NAME = re.compile(r"[A-Z]+")
COMMENT_MARK = "#"


def parse_line(number, line):
    """Разобрать одну строку ``A: B C`` в имя и его зависимости."""
    name, separator, rest = line.partition(":")
    name = name.strip()
    dependencies = rest.split()
    if not separator or not NAME.fullmatch(name):
        raise RepoError(f"line {number}: expected 'NAME: DEPENDENCIES'")
    for dependency in dependencies:
        if not NAME.fullmatch(dependency):
            raise RepoError(f"line {number}: bad package {dependency!r}")
    return name, dependencies


def parse_graph_text(text):
    """Разобрать описание в отображение имя -> зависимости."""
    graph = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split(COMMENT_MARK)[0].strip()
        if not line:
            continue
        name, dependencies = parse_line(number, line)
        known = graph.setdefault(name, [])
        known += [d for d in dependencies if d not in known]
        for dependency in dependencies:
            graph.setdefault(dependency, [])
    return graph


class GraphFileRepository:
    """Репозиторий на основе описания тестового графа."""

    def __init__(self, graph):
        """Сохранить отображение имя -> зависимости."""
        self.graph = graph

    @classmethod
    def from_file(cls, path):
        """Прочитать и разобрать файл тестового репозитория."""
        try:
            text = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise RepoError(f"cannot read {path}: {exc}") from exc
        return cls(parse_graph_text(text))

    def resolve(self, name):
        """Возвращает имя, если пакет описан, иначе None."""
        return name if name in self.graph else None

    def dependencies(self, name):
        """Возвращает прямые зависимости пакета."""
        return list(self.graph.get(name, []))