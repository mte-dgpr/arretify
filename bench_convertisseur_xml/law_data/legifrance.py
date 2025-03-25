import json
from typing import List, Dict, TypedDict
from pathlib import Path
from datetime import date

# Load settings to be sure that we provide 
# config to the legifrance package
from bench_convertisseur_xml.settings import LOGGER
from clients_api_droit.legifrance import authenticate, search_arrete

from .dev_cache import use_dev_cache


class CodeDatum(TypedDict):
    titre: str
    cid: str


class CodeIndexDatum(TypedDict):
    num: str
    id: str
    cid: str


CURRENT_DIR = Path(__file__).parent
LEGIFRANCE_DATA = CURRENT_DIR / 'legifrance'
_TOKENS: Dict | None = None


with open(LEGIFRANCE_DATA / 'codes.json', 'r', encoding='utf-8') as fd:
    CODES: List[CodeDatum] = json.loads(fd.read())['data']

CODE_INDEXES: Dict[str, List[CodeIndexDatum]] = {}
for code in CODES:
    code_index_file_path = LEGIFRANCE_DATA / f'code_index_{code['cid']}.json'
    try:
        with open(code_index_file_path, 'r', encoding='utf-8') as fd:
            code_index = json.loads(fd.read())['data']
    except FileNotFoundError:
        continue

    CODE_INDEXES[code['cid']] = code_index


def get_code_titles() -> List[str]:
    return [code['titre'] for code in CODES]


def get_code_id_with_title(title: str) -> str | None:
    for code in CODES:
        if code['titre'] == title:
            return code['cid']
    return None


def get_code_article_id_from_article_num(code_id: str, article_num: str) -> str | None:
    try:
        code_index = CODE_INDEXES[code_id]
    except KeyError:
        LOGGER.warning(f"Could not find code index for code {code_id}")
        return None

    for article in code_index:
        if article['num'] == article_num:
            return article['id']
    return None


@use_dev_cache
def get_arrete_legifrance_id(title: str, date: date) -> str | None:
    global _TOKENS
    if _TOKENS is None:
        _TOKENS = authenticate()
    for arrete in search_arrete(_TOKENS, title, date):
        arrete_cid = arrete['titles'][0]['cid']
        return arrete_cid
    return None