import re
from dataclasses import dataclass
from datetime import date
from typing import Literal, List, get_args, cast, TypedDict
from bs4 import BeautifulSoup

from ..settings import APP_ROOT, LOGGER
from .arretes import parse_arretes, ARRETE_IGNORE_RE


if __name__ == '__main__':
    import json
    contents = open(APP_ROOT / 'tmp' / 'arretes.json', 'r', encoding='utf-8').read()
    paragraphs_mentioning_arrete = json.loads(contents)
    soup = BeautifulSoup(features="html.parser")
    all_arretes_failed: List[str] = []

    paragraphs_html = []
    for paragraph in paragraphs_mentioning_arrete:
        paragraph_elements = parse_arretes(soup, paragraph)

        for element in paragraph_elements:
            if isinstance(element, str) and 'arrêté' in ARRETE_IGNORE_RE.sub('', element):
                all_arretes_failed.append(paragraph)
                break

        paragraph_html = ''.join([str(e) for e in paragraph_elements])
        paragraphs_html.append(paragraph_html)
        # import pdb; pdb.set_trace()


    with open(APP_ROOT / 'tmp' / 'arretes_failed.txt', 'w', encoding='utf-8') as fd:
        fd.write('\n\n'.join([str(r) for r in all_arretes_failed]))

    # LOGGER.info(f'found {len(all_arretes_refs)} arretes, failed {len(all_arretes_failed)}')