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
import logging
from pathlib import Path
from typing import Dict, Sequence, TypedDict

CURRENT_DIR = Path(__file__).parent
LEGIFRANCE_DATA = CURRENT_DIR / "legifrance"

_LOGGER = logging.getLogger(__name__)


class CodeDatum(TypedDict):
    titre: str
    cid: str


class CodeIndexDatum(TypedDict):
    num: str
    id: str
    cid: str


with open(LEGIFRANCE_DATA / "codes.json", "r", encoding="utf-8") as fd:
    CODES: Sequence[CodeDatum] = json.loads(fd.read())["data"]

CODE_INDEXES: Dict[str, Sequence[CodeIndexDatum]] = {}
for code in CODES:
    code_index_file_path = LEGIFRANCE_DATA / f"code_index_{code['cid']}.json"
    try:
        with open(code_index_file_path, "r", encoding="utf-8") as fd:
            code_index = json.loads(fd.read())["data"]
    except FileNotFoundError:
        continue

    CODE_INDEXES[code["cid"]] = code_index


def get_code_titles() -> list[str]:
    return [code["titre"] for code in CODES]


def get_code_id_with_title(title: str) -> str | None:
    for code in CODES:
        if code["titre"] == title:
            return code["cid"]
    return None


def get_code_article_id_from_article_num(code_id: str, article_num: str) -> str | None:
    try:
        code_index = CODE_INDEXES[code_id]
    except KeyError:
        _LOGGER.warning(f"Could not find code index for code {code_id}")
        return None

    for article in code_index:
        if article["num"] == article_num:
            return article["id"]
    return None
