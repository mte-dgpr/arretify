"""
Simple cache system to avoid calling the API too often.
It is not concurrent safe, **to be used only in development mode**.
"""

import json
from pathlib import Path
from functools import wraps
import logging
from typing import (
    Any,
    TypeVar,
    ParamSpec,
    cast,
    Callable,
    Concatenate,
    Dict,
)

from arretify.types import ParsingContext


R = TypeVar("R")
P = ParamSpec("P")

CacheDict = Dict[
    # Function name
    str,
    Dict[
        # Function parameters
        str,
        Any,
    ],
]


_CACHE: CacheDict = {}
_CACHE_FILE_PATH = Path(__file__).parent / "dev_cache.json"
_LOGGER = logging.getLogger(__name__)


# Load cache from file if it exists
def _ensure_cache() -> CacheDict:
    global _CACHE
    if _CACHE_FILE_PATH.exists():
        with open(_CACHE_FILE_PATH, "r", encoding="utf8") as f:
            _CACHE = json.load(f)
        return _CACHE
    else:
        raise ValueError(f"Cache file {_CACHE_FILE_PATH} not found")


def use_dev_cache(
    func: Callable[Concatenate[ParsingContext, P], R],
) -> Callable[Concatenate[ParsingContext, P], R]:
    @wraps(func)
    def wrapper(parsing_context: ParsingContext, *args: P.args, **kwargs: P.kwargs) -> R:
        if parsing_context.settings.env == "development":
            try:
                return _get_cached_value(func, *args, **kwargs)
            except KeyError as err:
                _LOGGER.info(f"{err}, calling real API ...")
                value = func(parsing_context, *args, **kwargs)
                _set_cached_value(func, value, *args, **kwargs)
                return value
        else:
            return func(parsing_context, *args, **kwargs)

    return wrapper


def _get_cached_value(
    func: Callable[Concatenate[ParsingContext, P], R], *args: P.args, **kwargs: P.kwargs
) -> R:
    cache = _ensure_cache()
    func_key = _get_func_key(func)
    params_key = _get_params_key(func, *args, **kwargs)
    if func_key not in cache:
        cache[func_key] = {}

    if params_key in cache[func_key]:
        return cast(R, cache[func_key][params_key])
    else:
        raise KeyError(f"Cache miss for {func_key}{params_key}")


def _set_cached_value(
    func: Callable[Concatenate[ParsingContext, P], R], value: R, *args: P.args, **kwargs: P.kwargs
) -> None:
    cache = _ensure_cache()
    func_key = _get_func_key(func)
    params_key = _get_params_key(func, *args, **kwargs)
    if func_key not in cache:
        cache[func_key] = {}
    cache[func_key][params_key] = value
    with open(_CACHE_FILE_PATH, "w", encoding="utf8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)


def _get_func_key(func: Callable[Concatenate[ParsingContext, P], R]) -> str:
    return func.__name__


def _get_params_key(
    func: Callable[Concatenate[ParsingContext, P], R], *args: P.args, **kwargs: P.kwargs
):
    args_key = ", ".join(str(arg) for arg in args)
    kwargs_key = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    params_key = f"({args_key}"
    if kwargs:
        params_key += f", {kwargs_key}"
    params_key += ")"
    return params_key
