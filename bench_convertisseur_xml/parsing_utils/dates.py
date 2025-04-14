from datetime import date, datetime
from bs4 import BeautifulSoup, Tag

from bench_convertisseur_xml.html_schemas import DATE_SCHEMA
from bench_convertisseur_xml.utils.html import make_data_tag
from bench_convertisseur_xml.regex_utils import (
    regex_tree,
    join_with_or,
    iter_regex_tree_match_strings,
)
from bench_convertisseur_xml.regex_utils.helpers import (
    lookup_normalized_version,
)


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


DATE_NODE = regex_tree.Group(
    regex_tree.Sequence(
        [
            regex_tree.Branching(
                [
                    r"(((?P<day_first>1er)|(?P<day>\d{1,2})) (?P<month_name>"
                    + join_with_or(MONTH_NAMES)
                    + r") ((?P<year>\d{4})|(?P<year_2digits>\d{2})))",
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


def _handle_date_match_dict(match_dict: regex_tree.MatchDict) -> date:
    if match_dict.get("month_name"):
        match_month = lookup_normalized_version(MONTH_NAMES, match_dict["month_name"])
        try:
            month = MONTH_NAMES.index(match_month) + 1
        except ValueError:
            raise RuntimeError(f'couldnt find month for "{match_month}"')
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

    return date(
        day=day,
        month=month,
        year=year,
    )


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
    date_object = _handle_date_match_dict(regex_tree_match.match_dict)
    date_container = make_data_tag(
        soup,
        DATE_SCHEMA,
        contents=iter_regex_tree_match_strings(regex_tree_match),
    )
    date_container["datetime"] = render_date_str(date_object)
    return date_container
