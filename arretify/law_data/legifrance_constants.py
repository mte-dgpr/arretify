import json
from pathlib import Path
from typing import Dict, List, TypedDict
from arretify.settings import LOGGER

CURRENT_DIR = Path(__file__).parent
LEGIFRANCE_DATA = CURRENT_DIR / "legifrance"


class CodeDatum(TypedDict):
    titre: str
    cid: str


class CodeIndexDatum(TypedDict):
    num: str
    id: str
    cid: str


with open(LEGIFRANCE_DATA / "codes.json", "r", encoding="utf-8") as fd:
    CODES: List[CodeDatum] = json.loads(fd.read())["data"]

CODE_INDEXES: Dict[str, List[CodeIndexDatum]] = {}
for code in CODES:
    code_index_file_path = LEGIFRANCE_DATA / f"code_index_{code['cid']}.json"
    try:
        with open(code_index_file_path, "r", encoding="utf-8") as fd:
            code_index = json.loads(fd.read())["data"]
    except FileNotFoundError:
        continue

    CODE_INDEXES[code["cid"]] = code_index


def get_code_titles() -> List[str]:
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
        LOGGER.warning(f"Could not find code index for code {code_id}")
        return None

    for article in code_index:
        if article["num"] == article_num:
            return article["id"]
    return None
