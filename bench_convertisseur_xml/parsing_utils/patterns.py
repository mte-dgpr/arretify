import re

from bench_convertisseur_xml.regex_utils import PatternProxy


ET_VIRGULE_PATTERN_S = r"(\s*(,|,?et)\s*)"

# "°" is a common OCR error for superscript "è"
# as in "4ᵉ" for "4ème".
EME_PATTERN_S = r"(er|ème|è|°|ᵉ)"

ORDINAL_PATTERN_S = (
    r"(premier)|(deuxième|second)|(troisième)|(quatrième)|(cinquième)|(sixième)"
    r"|(septi[eè]me)|(huitième)|(neuvième)|(dixième)|(onzième)|(douzième)|(treizième)"
)

ORDINAL_PATTERN = PatternProxy(ORDINAL_PATTERN_S)


def ordinal_str_to_int(ordinal: str) -> int:
    ordinal_match = re.match(ORDINAL_PATTERN_S, ordinal)
    if not ordinal_match:
        raise RuntimeError("Ordinal match unexpectedly failed")

    for i in range(1, len(ordinal_match.groups()) + 1):
        if ordinal_match.group(i):
            return i

    raise RuntimeError(f"Ordinal not found {ordinal}")
