#
# Copyright (c) 2025 Direction générale de la prévention des risques (DGPR).
#
# This file is part of Arrêtify.
# See https://github.com/mte-dgpr/arretify for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import logging
from enum import Enum
from functools import wraps
from typing import Callable, Concatenate, ParamSpec, Type, TypeVar, Union

from arretify.types import DocumentContext

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
    non_existant_date = "non_existant_date"
    """This date is syntactically valid but doesn't exist on the calendar"""
    unknown_content = "unknown_content"
    """Content that could not be categorized according to the expected structure"""


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
        func: Callable[Concatenate[DocumentContext, P], None],
    ) -> Callable[Concatenate[DocumentContext, P], None]:
        @wraps(func)
        def wrapper(document_context: DocumentContext, *args: P.args, **kwargs: P.kwargs) -> None:
            try:
                func(document_context, *args, **kwargs)
            except ArretifyError as error:
                logger.warning(
                    f"{error.code.value} - {error}",
                )

        return wrapper

    return decorator
