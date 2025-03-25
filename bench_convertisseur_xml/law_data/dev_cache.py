"""
Simple cache system to avoid calling the API too often. 
It is not concurrent safe, **to be used only in development mode**.
"""
import unittest
import json
import os
from pathlib import Path
from functools import wraps
from typing import TypeVar, ParamSpec, Tuple, Union, cast, Callable, Dict, List, Tuple, Type, Iterator
from importlib import import_module

from bench_convertisseur_xml.settings import LOGGER, ENV


R = TypeVar('R')
P = ParamSpec('P')

_CACHE_FILE_PATH = Path(__file__).parent / 'dev_cache.json'

# Load cache from file if it exists
if ENV == "development":
    if _CACHE_FILE_PATH.exists():
        with open(_CACHE_FILE_PATH, 'r', encoding='utf8') as f:
            _CACHE = json.load(f)
    else:
        raise ValueError(f"Cache file {_CACHE_FILE_PATH} not found")


def use_dev_cache(func: Callable[P, R]) -> Callable[P, R]:
    if ENV == 'development':
        LOGGER.info(f"{ENV} mode detected, using cache for {func.__name__}")
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if ENV == 'development':
            try:
                return _get_cached_value(func, args, kwargs)
            except KeyError as err:
                LOGGER.info(f"{err}, calling real API ...")
                value = func(*args, **kwargs)
                _set_cached_value(func, args, kwargs, value)
                return value
        else:
            return func(*args, **kwargs)
    return wrapper


def _get_cached_value(func: Callable[P, R], args: P.args, kwargs: P.kwargs) -> R:
    func_key = _get_func_key(func)
    params_key = _get_params_key(args, kwargs)
    if func_key not in _CACHE:
        _CACHE[func_key] = {}

    if params_key in _CACHE[func_key]:
        return cast(R, _CACHE[func_key][params_key])
    else:
        raise KeyError(f"Miss for {func_key}{params_key}")


def _set_cached_value(func: Callable[P, R], args: P.args, kwargs: P.kwargs, value: R) -> None:
    func_key = _get_func_key(func)
    params_key = _get_params_key(args, kwargs)
    if func_key not in _CACHE:
        _CACHE[func_key] = {}
    _CACHE[func_key][params_key] = value
    with open(_CACHE_FILE_PATH, 'w', encoding='utf8') as f:
        json.dump(_CACHE, f, ensure_ascii=False, indent=4)


def _get_func_key(func: Callable[P, R]) -> str:
    return func.__name__


def _get_params_key(args: P.args, kwargs: P.kwargs):
    args_key = ", ".join(str(arg) for arg in args)
    kwargs_key = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    params_key = f"({args_key}"
    if kwargs:
        params_key += f", {kwargs_key}"
    params_key += ")"
    return params_key