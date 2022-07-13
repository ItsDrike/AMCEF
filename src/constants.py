from typing import Optional, cast

from decouple import config
from fastapi.templating import Jinja2Templates


def _str_config(search_path: str, *args, **kwargs) -> str:
    """Shorthand to obtain configuration as string type-wise."""
    obj = config(search_path, *args, **kwargs)
    return cast(str, obj)


class Logging:
    """Logging related configuration"""

    DEBUG = bool(config("DEBUG", default=False))
    LOG_FILE = cast(Optional[str], config("LOG_FILE", default=None))
    MAX_FILE_SIZE = cast(int, config("LOG_FILE_MAX_SIZE", default=-1))


class Connection:
    """Config related to external connections (such as to a database)."""

    DATABASE_URL = _str_config("DATABASE_URL")
    API_BASE_URL = _str_config("API_BASE_URL", default="https://jsonplaceholder.typicode.com")


class Server:
    """Configuration related to the API server itself."""

    JWT_SECRET = _str_config("JWT_SECRET")
    SHOW_ADMIN_ENDPOINTS = Logging.DEBUG
    TEMPLATES = Jinja2Templates(directory="src/templates")
