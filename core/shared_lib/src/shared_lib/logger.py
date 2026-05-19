import logging
import sys

from shared_lib.config import config

RESET = "\033[0m"
GREY = "\033[38;5;245m"

COLORS = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m",
    "orange": "\033[38;5;208m",
}


def _resolve_color(value: str | None) -> str | None:
    """Convierte un nombre de color al código ANSI correspondiente"""
    if value is None:
        return None
    if value.startswith("\033"):
        return value
    return COLORS.get(value.lower())


class _PipelineFormatter(logging.Formatter):
    """
    Formato:  timestamp | proyecto | LEVEL [módulo] mensaje
    """

    _BASE_FMT = "%(asctime)s | {project:<10} | %(levelname)-8s [%(module)s] %(message)s"
    _DATE_FMT = "%Y-%m-%d %H:%M:%S"

    def __init__(
        self,
        project: str,
        *,
        warn_color: str | None = None,
        error_color: str | None = None,
        critical_color: str | None = None,
    ) -> None:
        super().__init__(
            fmt=self._BASE_FMT.format(project=project),
            datefmt=self._DATE_FMT,
        )
        self._level_colors: dict[int, str | None] = {
            logging.WARNING: _resolve_color(warn_color),
            logging.ERROR: _resolve_color(error_color),
            logging.CRITICAL: _resolve_color(critical_color),
        }

    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        color = self._level_colors.get(record.levelno)
        if color:
            return f"{color}{text}{RESET}"
        return text


def get_logger(
    project: str,
    *,
    warn_color: str = "yellow",
    error_color: str = "red",
    critical_color: str = "bright_red",
) -> logging.Logger:
    """Devuelve un logger configurado para el proyecto"""
    logger = logging.getLogger(f"pipeline.{project}")

    if logger.handlers:
        return logger

    level = config.log_levels.get(project, config.log_level)
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        _PipelineFormatter(
            project,
            warn_color=warn_color,
            error_color=error_color,
            critical_color=critical_color,
        )
    )
    logger.addHandler(handler)
    logger.propagate = False

    return logger
