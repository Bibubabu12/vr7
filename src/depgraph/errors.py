"""Исключения, вызываемые инструментом."""


class DepGraphError(Exception):
    """Базовый класс для всех ожидаемых ошибок инструмента."""


class ConfigError(DepGraphError):
    """Переданный пользователем параметр отсутствует или недействителен."""


class RepoError(DepGraphError):
    """Репозиторий не может быть прочитан или не содержит пакет."""


class GraphError(DepGraphError):
    """Граф зависимостей не может быть построен."""


class RenderError(DepGraphError):
    """Изображение графа не может быть создано."""