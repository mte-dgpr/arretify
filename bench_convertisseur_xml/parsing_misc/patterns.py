import re

APOSTROPHE_PATTERN_S = r"['’]"

ET_VIRGULE_PATTERN_S = r'(\s*(,|,?et)\s*)'

EME_PATTERN_S = r'(er|ème|è)'

ORDINAL_PATTERN_S = r'(premier)|(deuxi[èe]me|second)|(troisi[èe]me)|(quatri[èe]me)|(cinqui[èe]me)|(sixi[èe]me)|(septi[eè]me)|(huiti[èe]me)|(neuvi[èe]me)|(dixi[èe]me)|(onzi[èe]me)|(douzi[èe]me)|(treizi[èe]me)'

def ordinal_str_to_int(ordinal: str) -> str:
    ordinal_match = re.match(ORDINAL_PATTERN_S, ordinal)
    if not ordinal_match:
        raise RuntimeError('Ordinal match unexpectedly failed')
    
    for i in range(1, len(ordinal_match.groups()) + 1):
        if ordinal_match.group(i):
            return str(i)
    
    raise RuntimeError(f'Ordinal not found {ordinal}')