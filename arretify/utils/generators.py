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
from collections.abc import Callable
from typing import Any, cast


# REF : https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators
def remove_empty_strings_from_flow[F: Callable[..., Any]](
    func: F,
) -> F:
    def wrapper(*args, **kwargs):
        for element in func(*args, **kwargs):
            if not isinstance(element, str):
                yield element
            elif element:
                yield element

    return cast(F, wrapper)
