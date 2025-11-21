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
from typing import Callable, Iterator, cast

from arretify.types import ProtectedTag, ProtectedTagOrStr
from arretify.utils.element_ranges import (
    get_contiguous_elements_left as get_contiguous_elements_left_unprotected,
)
from arretify.utils.element_ranges import (
    get_contiguous_elements_right as get_contiguous_elements_right_unprotected,
)
from arretify.utils.element_ranges import (
    iter_collapsed_range_left as iter_collapsed_range_left_unprotected,
)
from arretify.utils.element_ranges import (
    iter_collapsed_range_right as iter_collapsed_range_right_unprotected,
)

ProtectedElementRange = list[ProtectedTagOrStr]

get_contiguous_elements_left = cast(
    Callable[[ProtectedTag], list[ProtectedTagOrStr]], get_contiguous_elements_left_unprotected
)
get_contiguous_elements_right = cast(
    Callable[[ProtectedTag], list[ProtectedTagOrStr]], get_contiguous_elements_right_unprotected
)
iter_collapsed_range_right = cast(
    Callable[[ProtectedTag], Iterator[ProtectedElementRange]],
    iter_collapsed_range_right_unprotected,
)
iter_collapsed_range_left = cast(
    Callable[[ProtectedTag], Iterator[ProtectedElementRange]], iter_collapsed_range_left_unprotected
)
