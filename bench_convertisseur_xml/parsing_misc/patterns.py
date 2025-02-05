import re

from bench_convertisseur_xml.regex_utils import PatternProxy


ET_VIRGULE_PATTERN_S = r'(\s*(,|,?et)\s*)'

# "°" is a common OCR error for superscript "è"
# as in "4ᵉ" for "4ème".
EME_PATTERN_S = r'(er|ème|è|°|ᵉ)'

ORDINAL_PATTERN_S = r'(premier)|(deuxième|second)|(troisième)|(quatrième)|(cinquième)|(sixième)|(septième)|(huitième)|(neuvième)|(dixième)|(onzième)|(douzième)|(treizième)'

ORDINAL_PATTERN = PatternProxy(ORDINAL_PATTERN_S)

# (?=.) lookahead to ensure at least one character is present
ROMAN_NUMERALS_S = r"(?=[IVXLCDM])M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})(?=\b)"



def ordinal_str_to_int(ordinal: str) -> str:
    ordinal_match = re.match(ORDINAL_PATTERN_S, ordinal)
    if not ordinal_match:
        raise RuntimeError('Ordinal match unexpectedly failed')
    
    for i in range(1, len(ordinal_match.groups()) + 1):
        if ordinal_match.group(i):
            return str(i)
    
    raise RuntimeError(f'Ordinal not found {ordinal}')