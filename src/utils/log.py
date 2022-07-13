import logging
import logging.handlers
import os
from pathlib import Path

import coloredlogs

from src.constants import Logging

LOG_LEVEL = logging.DEBUG if Logging.DEBUG else logging.INFO
LOG_FILE = Logging.LOG_FILE
LOG_FILE_MAX_SIZE = Logging.MAX_FILE_SIZE if Logging.MAX_FILE_SIZE != -1 else None
LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)7s | %(message)s"


def setup_logging() -> None:
    """
    Sets up logging library to use our logging configuration.

    This function should only be called once at the start of the program.
    """
    root_log = logging.getLogger()
    _setup_coloredlogs(root_log)
    _setup_logfile(root_log)
    root_log.setLevel(LOG_LEVEL)


def _setup_coloredlogs(root_log: logging.Logger) -> None:
    """Set up coloredlogs to use our log format and install it."""
    if "COLOREDLOGS_LOG_FORMAT" not in os.environ:
        coloredlogs.DEFAULT_LOG_FORMAT = LOG_FORMAT

    if "COLOREDLOGS_LEVEL_STYLES" not in os.environ:
        coloredlogs.DEFAULT_LEVEL_STYLES = {
            **coloredlogs.DEFAULT_LEVEL_STYLES,
            "critical": {"background": "red"},
        }

    coloredlogs.install(level=logging.DEBUG, logger=root_log)


def _setup_logfile(root_log: logging.Logger) -> None:
    """Setup a file handler for logging using our log format."""
    if LOG_FILE is not None:
        if LOG_FILE_MAX_SIZE is not None:
            file_handler = logging.handlers.RotatingFileHandler(Path(LOG_FILE), maxBytes=LOG_FILE_MAX_SIZE)
        else:
            file_handler = logging.FileHandler(Path(LOG_FILE))

        log_formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(log_formatter)
        root_log.addHandler(file_handler)
