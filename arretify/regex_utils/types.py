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
from dataclasses import dataclass
from types import EllipsisType
from typing import Tuple

PatternString = str
GroupName = str
QuantifierRange = Tuple[int, int | EllipsisType]


@dataclass(frozen=True)
class MatchNamedGroup:
    group_name: str
    text: str


@dataclass(frozen=True)
class Settings:
    ignore_case: bool = True
    ignore_accents: bool = True
    normalize_quotes: bool = True
    normalize_dashes: bool = True
