from collections.abc import Callable
from typing import NewType, Optional, TypeVar, Union, cast, overload

from decouple import config
from fastapi.templating import Jinja2Templates

T = TypeVar("T")
V = TypeVar("V")
Sentinel = NewType("Sentinel", object)
_MISSING = cast(Sentinel, object())


@overload
def _get_config(search_path: str, cast: None = None, default: Union[V, Sentinel] = _MISSING) -> Union[str, V]:
    ...


@overload
def _get_config(search_path: str, cast: Callable[[str], T], default: Union[V, Sentinel] = _MISSING) -> Union[T, V]:
    ...


def _get_config(
    search_path: str,
    cast: Optional[Callable[[str], object]] = None,
    default: object = _MISSING,
) -> object:
    """Wrapper around decouple.config that can handle typing better."""
    if cast is None:
        cast = lambda x: x

    if default is not _MISSING:
        obj = config(search_path, cast=cast, default=default)
    else:
        obj = config(search_path, cast=cast)

    return obj


class Logging:
    """Logging related configuration"""

    DEBUG = _get_config("DEBUG", cast=bool, default=False)
    LOG_FILE = _get_config("LOG_FILE", default=None)
    MAX_FILE_SIZE = _get_config("LOG_FILE_MAX_SIZE", cast=int, default=-1)


class Connection:
    """Config related to external connections (such as to a database)."""

    DATABASE_URL = _get_config("DATABASE_URL")
    REDIS_URL = _get_config("REDIS_URL")
    API_BASE_URL = _get_config("API_BASE_URL", default="https://jsonplaceholder.typicode.com")


class Server:
    """Configuration related to the API server itself."""

    JWT_SECRET = _get_config("JWT_SECRET")
    SHOW_ADMIN_ENDPOINTS = Logging.DEBUG
    TEMPLATES = Jinja2Templates(directory="src/templates")
