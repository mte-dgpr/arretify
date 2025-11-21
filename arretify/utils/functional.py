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
from functools import reduce, wraps
from typing import Callable, Iterable, Iterator, ParamSpec, Sequence, TypeVar, Union

T1 = TypeVar("T1")
T2 = TypeVar("T2")
P = ParamSpec("P")


def flat_map_string(
    elements: Iterable[Union[T1, str]],
    map_func: Callable[[str], Iterable[T1 | str]],
) -> Iterator[T1 | str]:
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


def iter_func_to_list(func: Callable[P, Iterable[T1]]) -> Callable[P, list[T1]]:
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
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> list[T1]:
        return list(func(*args, **kwargs))

    return wrapped


def chain_functions(
    context: T1,
    elements: T2,
    functions: Sequence[Callable[[T1, T2], T2]],
) -> T2:
    """
    Chains a list of functions to be applied sequentially to an initial value.
    Each function in the list takes the output of the previous function as input.
    """
    return reduce(
        lambda elements, func: func(context, elements),
        functions,
        elements,
    )
