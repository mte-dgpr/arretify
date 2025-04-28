import re
from unicodedata import normalize

from pylatexenc.latex2text import LatexNodes2Text

from arretify.parsing_utils.source_mapping import (
    TextSegment,
    apply_to_segment,
)
from arretify.regex_utils import sub_with_match
from .markdown_parsing import LIST_PATTERN, is_table_line


LATEX_NODE = LatexNodes2Text(keep_comments=True)


def _underscript_numbers_replacement(match):
    underscripts = "₀₁₂₃₄₅₆₇₈₉"
    return underscripts[int(match.group(1))]


def _superscript_numbers_replacement(match):
    superscripts = {
        "0": "⁰",
        "1": "¹",
        "2": "²",
        "3": "³",
        "4": "⁴",
        "5": "⁵",
        "6": "⁶",
        "7": "⁷",
        "8": "⁸",
        "9": "⁹",
    }
    return superscripts[match.group(1)]


def _math_bold_replacement(match):
    return normalize("NFKD", match.group(0))


def _resolve_diacritics(text: str):
    # Canonical decomposition
    text = normalize("NFD", text)

    # Catch first diacritic if several
    def replace_multiple_diacritics(match):
        letter = match.group(1)
        diacritics = match.group(0)[1:2]
        return letter + diacritics

    # Replace several diacritics by only one
    text = re.sub(r"([a-zA-Z])[\u0300-\u036F]{2,}", replace_multiple_diacritics, text)

    # Compose back
    text = normalize("NFC", text)

    return text


def _make_sub_wrong(wrong: str, correct: str):
    return lambda contents: re.sub(wrong, correct, contents)


def _convert_latex(match) -> str:

    contents = match.group(1)

    # Pre-requisites to convert LaTeX:
    # - Remove any '\\'
    contents = re.sub(r"\\{2,}", "", contents)

    # Convert LaTeX OCR to plain text
    contents = LATEX_NODE.latex_to_text(contents)

    # Supplementary steps to convert remnants of LaTeX conversion:
    # - Remove any ^ if not followed by a number
    contents = re.sub(r"\^(?![0-9])", "", contents)

    # - Remove indivisible whitespaces
    contents = re.sub(r" ", "", contents)

    # - Convert all _n to small n
    contents = re.sub(r"_([0-9])", _underscript_numbers_replacement, contents)

    # - Convert all ^n to upper n
    contents = re.sub(r"\^([0-9])", _superscript_numbers_replacement, contents)

    # - Convert any '∘' to '°'
    contents = re.sub(r"∘", "°", contents)

    # - Convert math bold characters
    contents = re.sub(
        r"[𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗]",
        _math_bold_replacement,
        contents,
    )

    # - Convert multiplication sign
    contents = re.sub(r"×", "x", contents)

    return contents


# TODO-PROCESS-TAG
def clean_markdown(line: TextSegment) -> TextSegment:

    # Remove newline at the end
    line = apply_to_segment(line, _make_sub_wrong(r"[\n\r]+$", ""))

    # Remove * at the beginning only if matching closing * found
    matched_em_open = re.search(r"^\s*(?P<em_open>\*+)(?!\s)", line.contents)

    line_mem: TextSegment
    if matched_em_open:
        asterisk_count = len(matched_em_open.group("em_open"))
        line_mem = line
        line = apply_to_segment(
            line,
            lambda contents: sub_with_match(contents, matched_em_open, "em_open"),
        )
        matched_em_close = re.search(
            r"\s*(?P<em_close>\*" + f"{{{asterisk_count}}})\b*",
            line.contents,
        )
        # If there's no matching closing asterisks, we restore the line
        if not matched_em_close or matched_em_close.start() == 0:
            line = line_mem
        else:
            line = apply_to_segment(
                line,
                lambda contents: sub_with_match(contents, matched_em_close, "em_close"),
            )

    # Remove any number of # or whitespaces at the beginning of the sentence
    if not LIST_PATTERN.match(line.contents):
        line = apply_to_segment(line, _make_sub_wrong(r"^\s*[#\s]+", ""))

    # Convert from latex to plain text
    line = apply_to_segment(
        line,
        lambda contents: re.sub(r"\$(.*?)\$", _convert_latex, contents),
    )

    # Resolve diacritics
    line = apply_to_segment(line, _resolve_diacritics)

    # Resolve specific OCR mismatches
    ocr_replacements = {
        r"n̊": "n°",
        r"N̊": "N°",
        r"Nํ": "N°",
        r"ı": "i",
    }
    for wrong, correct in ocr_replacements.items():
        line = apply_to_segment(line, _make_sub_wrong(wrong, correct))

    # Convert any '\%' to '%'
    line = apply_to_segment(line, _make_sub_wrong(r"\\%", "%"))

    # Remove <br> tags outside of tables, since the latter are rendered correctly
    if not is_table_line(line.contents):
        line = apply_to_segment(line, _make_sub_wrong(r"<br>", ""))

    return line
