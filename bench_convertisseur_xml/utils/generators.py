from collections.abc import Callable
from typing import Any, cast

from .html import PageElementOrString


# REF : https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators
def remove_empty_strings_from_flow[F: Callable[..., Any]](func: F) -> F:
    def wrapper(*args, **kwargs):
        for element in func(*args, **kwargs):
            if not isinstance(element, str):
                yield element
            elif element:
                yield element
    return cast(F, wrapper)