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
from typing import Iterable, Iterator, Union, Callable, TypeVar, ParamSpec, List
from functools import wraps, reduce

from arretify.types import DocumentContext


P = TypeVar("P")
T = ParamSpec("T")


def flat_map_string(
    elements: Iterable[Union[P, str]],
    map_func: Callable[[str], Iterable[P | str]],
) -> Iterator[P | str]:
    """
    Example:
        >>> elements = ["string", 2, "another", 3]
        >>> def map_func(x): return [x.upper()]
        >>> list(flat_map_string(elements, map_func))
        ['STRING', 2, 'ANOTHER', 3]
    """
    for element in elements:
        if isinstance(element, str):
            yield from map_func(element)
        else:
            yield element


def iter_func_to_list(func: Callable[T, Iterable[P]]) -> Callable[T, List[P]]:
    """
    Converts a function that returns an iterable into a function that returns a list.

    Example:
        >>> @iter_func_to_list
        >>> def my_iterable(a: int, b: int, c: int) -> range:
        ...     return range(a, b, c)
        >>> my_list_func = iter_func_to_list(my_iterable)
        >>> my_list_func(1, 10, 2)
        [1, 3, 5, 7, 9]
    """

    @wraps(func)
    def wrapped(*args: T.args, **kwargs: T.kwargs) -> List[P]:
        return list(func(*args, **kwargs))

    return wrapped


def chain_functions(
    context: DocumentContext,
    elements: P,
    functions: List[Callable[[DocumentContext, P], P]],
) -> P:
    """
    Chains a list of functions to be applied sequentially to an initial value.
    Each function in the list takes the output of the previous function as input.
    """
    return reduce(
        lambda elements, func: func(context, elements),
        functions,
        elements,
    )
