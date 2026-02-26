#
# Copyright (c) 2025 Direction générale de la prévention des risques (DGPR).
#
# This file is part of Arrêtify.
# See https://github.com/mte-dgpr/arretify for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import re
from typing import cast
from unicodedata import normalize

from pylatexenc.latex2text import LatexNodes2Text

from arretify.parsing_utils.dates import MONTH_POINT_ABBREVIATIONS
from arretify.regex_utils import join_with_or, lookup_normalized_version, regex_tree, sub_with_match
from arretify.utils.html_split_merge import make_regex_tree_splitter
from arretify.utils.markdown_parsing import BULLETPOINT_PATTERN_S, LIST_PATTERN, TABLE_LINE_PATTERN
from arretify.utils.split_merge import Splitter, split_and_map_elements
from arretify.utils.strings import merge_strings

LATEX_NODE = LatexNodes2Text(keep_comments=True)


FAILED_MONTH_POINT_ABBREVIATIONS = regex_tree.Group(
    regex_tree.Sequence(
        [
            r"\s",
            regex_tree.Literal(
                join_with_or(
                    [month_name.replace(".", r"") for month_name in MONTH_POINT_ABBREVIATIONS]
                ),
                key="month_name",
            ),
            r"(,)\s",
        ]
    ),
    group_name="__failed_month_point_abbreviation",
)


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


def _render_point_abbreviation_month(match: regex_tree.Match) -> str:
    month_name = match.match_dict["month_name"]
    for lookup_text in [month_name, month_name + "."]:
        try:
            return (
                " "
                + lookup_normalized_version(
                    MONTH_POINT_ABBREVIATIONS,
                    lookup_text,
                    settings=FAILED_MONTH_POINT_ABBREVIATIONS.settings,
                )
                + " "
            )
        except KeyError:
            continue
    raise KeyError(f"No match found for {month_name}")


def _clean_failed_month_abbreviations(line_contents: str) -> str:
    return merge_strings(
        split_and_map_elements(
            [line_contents],
            cast(
                Splitter[str, regex_tree.Match],
                make_regex_tree_splitter(FAILED_MONTH_POINT_ABBREVIATIONS),
            ),
            _render_point_abbreviation_month,
        )
    )


# TODO-PROCESS-TAG
def clean_markdown(line: str) -> str:

    # Remove newline at the end
    line = re.sub(r"[\n\r]+$", "", line)

    # Remove * at the beginning only if matching closing * found
    matched_em_open = re.search(
        rf"^{BULLETPOINT_PATTERN_S}?\s*(?P<em_open>\*+)(?!\s)",
        line,
    )

    line_mem: str
    if matched_em_open:
        asterisk_count = len(matched_em_open.group("em_open"))
        line_mem = line
        line = sub_with_match(line, matched_em_open, "em_open")
        matched_em_close = re.search(
            r"\s*(?P<em_close>\*" + f"{{{asterisk_count}}})\b*",
            line,
        )
        # If there's no matching closing asterisks, we restore the line
        if not matched_em_close or matched_em_close.start() == 0:
            line = line_mem
        else:
            line = sub_with_match(line, matched_em_close, "em_close")

    # Remove any number of # or whitespaces at the beginning of the sentence
    if not LIST_PATTERN.match(line):
        line = re.sub(r"^\s*[#\s]+", "", line)

    # Convert from latex to plain text
    line = re.sub(r"\$(.*?)\$", _convert_latex, line)

    # Resolve diacritics
    line = _resolve_diacritics(line)

    # Replace wrong month abbreviations
    line = _clean_failed_month_abbreviations(line)

    # Resolve specific OCR mismatches
    ocr_replacements = {
        r"n̊": "n°",
        r"N̊": "N°",
        r"Nํ": "N°",
        r"ı": "i",
        r"p̧i": "pti",
        r"p̣": "p",
        r"Y̌": "Y",
        r"g̣": "g",
        r"'́p": "p",
        r"º": "°",
    }
    for wrong, correct in ocr_replacements.items():
        line = re.sub(wrong, correct, line)

    # Convert any '\%' to '%'
    line = re.sub(r"\\%", "%", line)

    # Convert any '\&' to '&'
    line = re.sub(r"\\&", "&", line)

    # Remove <br> tags outside of tables, since the latter are rendered correctly
    if not TABLE_LINE_PATTERN.match(line):
        line = re.sub(r"<br>", "", line)

    # Remove footnotes detected by OCR
    line = re.sub(r"\[\^0\]\s*", "", line)

    return line
