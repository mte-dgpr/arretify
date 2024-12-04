import re
from dataclasses import dataclass
from datetime import date
from typing import Literal, List, get_args, cast, TypedDict

from ..settings import APP_ROOT, LOGGER
from .text_utils import remove_accents, normalize_text
from .arretes import ArreteReference, parse_arretes, ARRETE_RE_LIST


if __name__ == '__main__':
    import json
    contents = open(APP_ROOT / 'tmp' / 'arretes.json', 'r', encoding='utf-8').read()
    paragraphs_mentioning_arrete = json.loads(contents)
    all_arretes_refs: List[ArreteReference] = []
    all_arretes_failed: List[str] = []
    for paragraph in paragraphs_mentioning_arrete:
        arretes_refs, arretes_failed = parse_arretes(ARRETE_RE_LIST, paragraph)
        all_arretes_refs.extend(arretes_refs)
        if arretes_failed:
            all_arretes_failed.append(arretes_failed)
    # print('\n'.join([str(r) for r in all_arretes_refs]))

    with open(APP_ROOT / 'tmp' / 'arretes_failed.txt', 'w', encoding='utf-8') as fd:
        fd.write('\n\n'.join([str(r) for r in all_arretes_failed]))

    LOGGER.info(f'found {len(all_arretes_refs)} arretes, failed {len(all_arretes_failed)}')