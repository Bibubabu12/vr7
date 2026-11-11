"""Позволяет запускать инструмент с помощью ``python -m depgraph``."""

import sys

from .cli import main

sys.exit(main())
