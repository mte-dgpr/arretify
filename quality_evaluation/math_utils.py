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

from typing import Callable, TypeVar

U = TypeVar("U")


def compute_average_score(
    pairs: list[tuple[U, U]], score_function: Callable[[U, U], float]
) -> float:
    """
    Compute average score for matched pairs using the provided scoring function.
    Returns 0.0 if no pairs.
    """
    if not pairs:
        return 0.0
    scores = [score_function(first, second) for first, second in pairs]
    return sum(scores) / len(scores)
