"""Чтение индексов пакетов apt (файлов ``Packages``) Ubuntu/Debian."""

import gzip
import lzma
import zlib
from urllib.request import urlopen

from .errors import RepoError

TIMEOUT_SECONDS = 60
GZIP_MAGIC = b"\x1f\x8b"
XZ_MAGIC = b"\xfd7zXZ\x00"
NAME_FIELD = "Package"
PROVIDES_FIELD = "Provides"
DEPENDENCY_FIELDS = ("Pre-Depends", "Depends")
CONTINUATION = (" ", "\t")
VERSION_MARKS = "([<"


def download(url):
    """Возвращает байты, полученные по URL."""
    try:
        with urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            return response.read()
    except (OSError, ValueError) as exc:
        raise RepoError(f"не удалось скачать {url}: {exc}") from exc


def decompress(raw):
    """Возвращает текст индекса; gzip и xz определяются по сигнатуре (magic bytes)."""
    try:
        if raw.startswith(GZIP_MAGIC):
            raw = gzip.decompress(raw)
        elif raw.startswith(XZ_MAGIC):
            raw = lzma.decompress(raw)
    except (OSError, EOFError, zlib.error, lzma.LZMAError) as exc:
        raise RepoError(f"не удалось распаковать индекс пакетов: {exc}") from exc
    return raw.decode("utf-8", errors="replace")


def parse_stanza(block):
    """Разобрать один абзац ``Field: value`` в словарь."""
    fields = {}
    key = None
    for line in block.splitlines():
        if line.startswith(CONTINUATION):
            if key:
                fields[key] += " " + line.strip()
        elif ":" in line:
            key, _, value = line.partition(":")
            fields[key] = value.strip()
    return fields


def parse_index(text):
    """Возвращает отображение: имя пакета -> поля; первая запись сохраняется."""
    packages = {}
    for block in text.replace("\r\n", "\n").split("\n\n"):
        fields = parse_stanza(block)
        name = fields.get(NAME_FIELD)
        if name and name not in packages:
            packages[name] = fields
    return packages


def clean_name(text):
    """Удаляет информацию о версии, архитектуре и профиле из имени."""
    name = text
    for mark in VERSION_MARKS:
        name = name.split(mark)[0]
    return name.strip().split(":")[0]


def parse_dependency_field(value):
    """Разбивает значение поля зависимостей на группы альтернатив."""
    groups = []
    for part in value.split(","):
        names = [clean_name(alt) for alt in part.split("|")]
        names = [name for name in names if name]
        if names:
            groups.append(names)
    return groups


def build_providers(packages):
    """Сопоставляет имена виртуальных пакетов первому пакету, предоставляющему их."""
    providers = {}
    for name, fields in packages.items():
        for group in parse_dependency_field(fields.get(PROVIDES_FIELD, "")):
            providers.setdefault(group[0], name)
    return providers


class AptRepository:
    """Индекс пакетов apt-репозитория."""

    def __init__(self, packages):
        """Сохраняет разобранный индекс и строит карту виртуальных пакетов."""
        self.packages = packages
        self.providers = build_providers(packages)

    @classmethod
    def from_url(cls, url):
        """Скачивает и разбирает Packages, Packages.gz или Packages.xz."""
        return cls(parse_index(decompress(download(url))))

    def resolve(self, name):
        """Возвращает реальный пакет по имени или None, если он неизвестен."""
        if name in self.packages:
            return name
        return self.providers.get(name)

    def choose(self, group):
        """Выбирает первую альтернативу, присутствующую в индексе."""
        for name in group:
            resolved = self.resolve(name)
            if resolved:
                return resolved
        return group[0]

    def dependencies(self, name):
        """Возвращает прямые зависимости (Pre-Depends и Depends)."""
        fields = self.packages.get(name)
        if not fields:
            return []
        result = []
        for field in DEPENDENCY_FIELDS:
            for group in parse_dependency_field(fields.get(field, "")):
                choice = self.choose(group)
                if choice != name and choice not in result:
                    result.append(choice)
        return result