import json
from typing import List
from pathlib import Path
from datetime import date

# Load settings to be sure that we provide 
# config to the legifrance package
from bench_convertisseur_xml.settings import LOGGER
from clients_api_droit.legifrance import authenticate, search_arrete, build_arrete_site_url


CURRENT_DIR = Path(__file__).parent


with open(CURRENT_DIR / 'legifrance' / 'codes.json', 'r', encoding='utf-8') as fd:
    CODES = json.loads(fd.read())['data']


def get_code_titles() -> List[str]:
    return [code['titre'] for code in CODES]


def find_code_id_with_title(title: str) -> str | None:
    for code in CODES:
        if code['titre'] == title:
            return code['cid']
    return None


def get_arrete_legifrance_id(title: str, date: date) -> str | None:
    tokens = authenticate()
    for arrete in search_arrete(tokens, title, date):
        arrete_cid = arrete['titles'][0]['cid']
        return arrete_cid
    return None