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
import json
from pathlib import Path
from typing import Set

from arretify.regex_utils import Settings, normalize_string

CURRENT_DIR = Path(__file__).parent
FRENCH_ADDRESSES_DATA = CURRENT_DIR / "french_addresses"

WAY_TYPES = [
    "ruelle",
    "rue",
    "boulevard",
    "avenue",
    "place",
    "allée",
    "impasse",
    "quai",
    "voie",
    "chemin",
    "cours",
    "route",
    "sentier",
    "passage",
    "cité",
    "esplanade",
    "faubourg",
    "parvis",
    "promenade",
    "square",
    "traverse",
    "chaussée",
    "montée",
    "descente",
    "lieu dit",
    "résidence",
    "quartier",
    "pont",
]
"""Non-exhaustive list of French way types."""

NUMBER_SUFFIXES = [
    "bis",
    "ter",
    "quater",
    "quinquies",
    "sexies",
    "septies",
    "octies",
    "nonies",
]
"""Non-exhaustive list of French street number suffixes."""

STREET_NAMES_NORMALIZATION_SETTINGS = Settings()
"""Settings to use when normalizing street names for matching purposes."""

ALL_STREET_NAMES: Set[str]
"""Set of French street names extracted from the "Base Adresse Nationale" (BAN)."""

with open(FRENCH_ADDRESSES_DATA / "street_names.json", "r", encoding="utf-8") as f:
    # Normalize street names to remove duplicates.
    ALL_STREET_NAMES = {
        normalize_string(
            street_name,
            STREET_NAMES_NORMALIZATION_SETTINGS,
        )
        for street_name in json.loads(f.read())
    }
