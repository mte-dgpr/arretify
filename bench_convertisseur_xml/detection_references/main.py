import re
from dataclasses import dataclass
from datetime import date
from typing import Literal, List, get_args, cast, TypedDict
from bs4 import BeautifulSoup

from ..settings import APP_ROOT, LOGGER
from .arretes_references import parse_arretes_references, ARRETE_IGNORE_RE
from bench_convertisseur_xml.html_schemas import ARRETE_REFERENCE_SCHEMA


if __name__ == '__main__':
    import json
    contents = open(APP_ROOT / 'tmp' / 'arretes.json', 'r', encoding='utf-8').read()
    paragraphs_mentioning_arrete = json.loads(contents)
    soup = BeautifulSoup(features="html.parser")
    all_arretes_failed: List[str] = []

    paragraphs_html = []
    for paragraph in paragraphs_mentioning_arrete:
        paragraph_elements = parse_arretes_references(soup, [paragraph])

        for element in paragraph_elements:
            if isinstance(element, str) and 'arrêté' in ARRETE_IGNORE_RE.sub('', element):
                all_arretes_failed.append(paragraph)
                break

        paragraph_html = ''.join([str(e) for e in paragraph_elements])
        paragraphs_html.append(paragraph_html)

    with open(APP_ROOT / 'tmp' / 'arretes_failed.txt', 'w', encoding='utf-8') as fd:
        fd.write('\n\n'.join([str(r) for r in all_arretes_failed]))

    arretes_html = f"""<!DOCTYPE html>
<html>
<head>
  <style>
    .dsr-arrete {{
      color: rgb(255, 15, 95);
    }}
  </style>
</head>
<body>{''.join(paragraphs_html)}"""

    with open(APP_ROOT / 'tmp' / 'arretes_parsed.html', 'w', encoding='utf-8') as fd:
        fd.write(arretes_html)

    all_arretes_parsed = BeautifulSoup(arretes_html, features='html.parser').select('.dsr-arrete_reference')
    LOGGER.info(f'found {len(all_arretes_parsed)} arretes, failed {len(all_arretes_failed)}')