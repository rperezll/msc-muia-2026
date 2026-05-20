import logging

from rich.console import Console
from rich.logging import RichHandler

from shared_lib.config import config

_stderr = Console(stderr=True)

# Paleta de colores para diferenciar proyectos en consola
_PALETTE = [
    "bold cyan",
    "bold magenta",
    "bold green",
    "bold yellow",
    "bold blue",
    "bold bright_cyan",
    "bold bright_magenta",
    "bold bright_green",
]


def _project_style(project: str) -> str:
    return _PALETTE[hash(project) % len(_PALETTE)]


def get_logger(project: str) -> logging.Logger:
    """Devuelve un logger con salida rich por stderr. Color único por proyecto."""
    logger = logging.getLogger(f"pipeline.{project}")

    if logger.handlers:
        return logger

    level = config.log_levels.get(project, config.log_level)
    logger.setLevel(level)

    style = _project_style(project)
    handler = RichHandler(
        console=_stderr,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
        log_time_format="[%Y-%m-%d %H:%M:%S]",
    )
    handler.setFormatter(logging.Formatter(f"[{style}]\\[{project:<10}][/{style}] %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False

    return logger
