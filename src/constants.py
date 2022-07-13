from typing import Optional, cast

from decouple import config


class Logging:
    """Logging related configuration"""

    DEBUG = bool(config("DEBUG", default=False))
    LOG_FILE = cast(Optional[str], config("LOG_FILE", default=None))
    MAX_FILE_SIZE = cast(int, config("LOG_FILE_MAX_SIZE", default=-1))
