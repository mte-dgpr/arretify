from typing import Union, Callable, Type, TypeVar, ParamSpec, Concatenate
from enum import Enum
import logging

from arretify.types import ParsingContext
from functools import wraps


R = TypeVar("R")
P = ParamSpec("P")


class SettingsError(ValueError):
    pass


class DependencyError(ImportError):
    pass


class ErrorCodes(Enum):
    markdown_parsing = "markdown_parsing"
    unbalanced_quote = "unbalanced_quote"
    non_contiguous_titles = "non_contiguous_titles"
    law_data_api_error = "law_data_api_error"


class ArretifyError(Exception):

    def __init__(
        self,
        code: ErrorCodes,
        message: Union[str, None] = None,
    ):
        self.code = code
        super(ArretifyError, self).__init__(message if message else code.value)


def catch_and_convert_into_arretify_error(
    error_class: Type[Exception],
    to_error_code: ErrorCodes,
) -> Callable:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except error_class as e:
                raise ArretifyError(to_error_code, str(e)) from e

        return wrapper

    return decorator


def catch_and_log_arretify_error(
    logger: logging.Logger,
) -> Callable:
    def decorator(
        func: Callable[Concatenate[ParsingContext, P], None],
    ) -> Callable[Concatenate[ParsingContext, P], None]:
        @wraps(func)
        def wrapper(parsing_context: ParsingContext, *args: P.args, **kwargs: P.kwargs) -> None:
            try:
                func(parsing_context, *args, **kwargs)
            except ArretifyError as error:
                logger.warning(
                    f"{error.code.value} - {error}",
                )

        return wrapper

    return decorator
