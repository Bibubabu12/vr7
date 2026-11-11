"""Представление графа в формате Graphviz (DOT) и его рендеринг в PNG."""

import subprocess

from .errors import RenderError

DOT_COMMAND = "dot"
SUCCESS_CODE = 0
INDENT = "    "
ROOT_ATTRS = 'shape=box, style=filled, fillcolor="#cfe8ff"'
CYCLE_ATTRS = 'color=red, constraint=false'


def quote(name):
    """Возвращает имя в виде экранированного идентификатора DOT в кавычках."""
    escaped = name.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def node_lines(graph):
    """Возвращает инструкции DOT для узлов; корневой узел выделен."""
    lines = [f"{INDENT}{quote(graph.root)} [{ROOT_ATTRS}];"]
    lines += [
        f"{INDENT}{quote(name)};"
        for name in graph.nodes() if name != graph.root
    ]
    return lines


def edge_lines(graph):
    """Возвращает инструкции DOT для ребер; ребра циклов подсвечены красным."""
    cycles = set(graph.cycles)
    lines = []
    for name, dependencies in graph.edges.items():
        for dependency in dependencies:
            attrs = f" [{CYCLE_ATTRS}]" if (name, dependency) in cycles else ""
            edge = f"{quote(name)} -> {quote(dependency)}"
            lines.append(f"{INDENT}{edge}{attrs};")
    return lines


def to_dot(graph):
    """Возвращает текст Graphviz, описывающий граф зависимостей."""
    lines = ["digraph dependencies {", f"{INDENT}rankdir=LR;"]
    lines += node_lines(graph) + edge_lines(graph)
    lines.append("}")
    return "\n".join(lines) + "\n"


def render_png(dot_text, path):
    """Рендерит текст DOT в PNG-файл с помощью утилиты Graphviz ``dot``."""
    command = [DOT_COMMAND, "-Tpng", "-o", path]
    try:
        result = subprocess.run(
            command, input=dot_text, text=True,
            capture_output=True, check=False,
        )
    except OSError as exc:
        raise RenderError(
            f"cannot run Graphviz '{DOT_COMMAND}': {exc}"
        ) from exc
    if result.returncode != SUCCESS_CODE:
        raise RenderError(f"Graphviz failed: {result.stderr.strip()}")