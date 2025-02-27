import json
from typing import List
from pathlib import Path


CURRENT_DIR = Path(__file__).parent


with open(CURRENT_DIR / 'legifrance' / 'codes.json', 'r', encoding='utf-8') as fd:
    CODES = json.loads(fd.read())['data']


def get_code_titles() -> List[str]:
    return [code['titre'] for code in CODES]
