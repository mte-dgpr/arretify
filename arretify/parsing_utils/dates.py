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
import logging
from datetime import date, datetime
from typing import List, TypedDict

from bs4 import BeautifulSoup, Tag

from arretify.html_schemas import DATE_SCHEMA
from arretify.utils.html import make_data_tag, render_str_list_attribute
from arretify.regex_utils import (
    regex_tree,
    join_with_or,
    iter_regex_tree_match_strings,
)
from arretify.regex_utils.helpers import (
    lookup_normalized_version,
)
from arretify.types import DataElementDataDict
from arretify.errors import ErrorCodes


_LOGGER = logging.getLogger(__name__)


DATE_FORMAT = "%Y-%m-%d"

MONTH_NAMES = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]

MONTH_POINT_ABBREVIATIONS = [
    "janv.",
    "févr.",
    "mars",
    "avr.",
    "mai",
    "juin",
    "juill.",
    "août",
    "sept.",
    "oct.",
    "nov.",
    "déc.",
]

MONTH_CODE_3_CHARS = [
    "jan",
    "fév",
    "mar",
    "avr",
    "mai",
    "jun",
    "jul",
    "aoû",
    "sep",
    "oct",
    "nov",
    "déc",
]

DATE_NODE = regex_tree.Group(
    regex_tree.Sequence(
        [
            regex_tree.Branching(
                [
                    # Examples of valid date strings:
                    # 1er janvier 2023
                    # 3 mar 1999
                    # 15 févr. 2020
                    regex_tree.Sequence(
                        [
                            r"((?P<day_first>1er)|(?P<day>\d{1,2})) ",
                            regex_tree.Branching(
                                [
                                    r"(?P<month_name>" + join_with_or(MONTH_NAMES) + r")",
                                    r"(?P<month_point_abbreviation>"
                                    + join_with_or(MONTH_POINT_ABBREVIATIONS)
                                    + r")",
                                    r"(?P<month_code_3_chars>"
                                    + join_with_or(MONTH_CODE_3_CHARS)
                                    + r")",
                                ]
                            ),
                            r" ((?P<year>\d{4})|(?P<year_2digits>\d{2}))",
                        ]
                    ),
                    # Examples of valid date strings:
                    # 01/01/2023
                    # 3/3/99
                    # 15/2/20
                    r"((?P<day>\d{2})/(?P<month>\d{2})/((?P<year>\d{4})|(?P<year_2digits>\d{2})))",
                ]
            ),
            # Check that the date string is followed by a valid separator
            # so that we don't match strings like 54/67/1980/A.
            r"(?=\s|\.|$|,|\)|;)",
        ]
    ),
    group_name="__date",
)


class _DateDict(TypedDict):
    day: int
    month: int
    year: int


def _handle_date_match_dict(match_dict: regex_tree.MatchDict) -> _DateDict:
    if match_dict.get("month_name"):
        month = _get_month_index(match_dict["month_name"], MONTH_NAMES)
    elif match_dict.get("month_point_abbreviation"):
        month = _get_month_index(match_dict["month_point_abbreviation"], MONTH_POINT_ABBREVIATIONS)
    elif match_dict.get("month_code_3_chars"):
        month = _get_month_index(match_dict["month_code_3_chars"], MONTH_CODE_3_CHARS)
    elif match_dict.get("month"):
        month = int(match_dict["month"])
    else:
        raise RuntimeError("expected month")

    if match_dict.get("day_first"):
        day = 1
    elif match_dict.get("day"):
        day = int(match_dict["day"])
    else:
        raise RuntimeError("expected day")

    if match_dict.get("year_2digits"):
        year = parse_year_str(match_dict["year_2digits"])
    elif match_dict.get("year"):
        year = parse_year_str(match_dict["year"])
    else:
        raise RuntimeError("expected year")

    return dict(
        day=day,
        month=month,
        year=year,
    )


def _get_month_index(month: str, month_strings: List[str]) -> int:
    match_month = lookup_normalized_version(month_strings, month)
    try:
        return month_strings.index(match_month) + 1
    except ValueError:
        raise RuntimeError(f'couldnt find month for "{match_month}"')


def render_year_str(year: int) -> str:
    year_str = str(year)
    if len(year_str) != 4:
        raise ValueError(f"Invalid year {year}")
    return year_str


def parse_year_str(year_str: str) -> int:
    if len(year_str) == 4:
        return int(year_str)
    if len(year_str) == 2:
        return int(year_str) + (1900 if int(year_str) > (date.today().year - 2000 + 5) else 2000)
    else:
        raise ValueError(f"Invalid year string {year_str}")


def render_date_str(date_object: date) -> str:
    return date_object.strftime(DATE_FORMAT)


def parse_date_str(date_str: str) -> date:
    return datetime.strptime(date_str, DATE_FORMAT).date()


def render_date_regex_tree_match(soup: BeautifulSoup, regex_tree_match: regex_tree.Match) -> Tag:
    date_dict = _handle_date_match_dict(regex_tree_match.match_dict)
    data_dict: DataElementDataDict = dict()

    try:
        date_str = render_date_str(
            date(
                year=date_dict["year"],
                month=date_dict["month"],
                day=date_dict["day"],
            )
        )

    except ValueError:
        data_dict["error_codes"] = render_str_list_attribute([ErrorCodes.non_existant_date.value])
        date_str = render_date_str(
            date(
                year=1,
                month=1,
                day=1,
            )
        )
        _LOGGER.warning(f"Invalid date {date_dict}, using {date_str} instead")
        # Date formating requires a 4-digit year, so we pad it with zeros if necessary
        # This is a workaround for inconsistencies across different platforms :
        # https://stackoverflow.com/questions/79588208/why-does-strftimey-not-yield-a-4-digit-year-for-dates-1000-ad-in-python
        if len(date_str) < len("YYYY-MM-DD"):
            date_str = date_str.rjust(len("YYYY-MM-DD"), "0")

    date_container = make_data_tag(
        soup,
        DATE_SCHEMA,
        contents=iter_regex_tree_match_strings(regex_tree_match),
        data=data_dict,
    )
    date_container["datetime"] = date_str
    return date_container
