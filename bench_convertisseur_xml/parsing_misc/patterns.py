import re

from bench_convertisseur_xml.regex_utils import PatternProxy


ET_VIRGULE_PATTERN_S = r'(\s*(,|,?et)\s*)'

EME_PATTERN_S = r'(er|ème|è)'

ORDINAL_PATTERN_S = r'(premier)|(deuxième|second)|(troisième)|(quatrième)|(cinquième)|(sixième)|(septi[eè]me)|(huitième)|(neuvième)|(dixième)|(onzième)|(douzième)|(treizième)'

ORDINAL_PATTERN = PatternProxy(ORDINAL_PATTERN_S)


def ordinal_str_to_int(ordinal: str) -> str:
    ordinal_match = re.match(ORDINAL_PATTERN_S, ordinal)
    if not ordinal_match:
        raise RuntimeError('Ordinal match unexpectedly failed')
    
    for i in range(1, len(ordinal_match.groups()) + 1):
        if ordinal_match.group(i):
            return str(i)
    
    raise RuntimeError(f'Ordinal not found {ordinal}')