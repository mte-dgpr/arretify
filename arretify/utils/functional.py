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
from typing import Iterable, Iterator, Union, Callable, TypeVar


P = TypeVar("P")


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
