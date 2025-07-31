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
from typing import Iterable, TypeVar


T = TypeVar("T")


def merge_strings(
    elements: Iterable[T],
    strip_other_types: bool = False,
) -> str:
    merged_string: str = ""
    for element in elements:
        if isinstance(element, str):
            merged_string += element
        elif strip_other_types is True:
            continue
        else:
            raise ValueError(
                f"Unexpected element type in merge_strings: {str(element)} of type {type(element)}"
            )
    return merged_string
