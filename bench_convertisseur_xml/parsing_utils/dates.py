import re
import calendar
from datetime import date, datetime
from typing import Literal, List, get_args, cast, TypedDict, Pattern
from bs4 import BeautifulSoup, Tag

# Important so that locale is initialized
from bench_convertisseur_xml.settings import *
from bench_convertisseur_xml.html_schemas import DATE_SCHEMA
from bench_convertisseur_xml.utils.html import make_data_tag
from bench_convertisseur_xml.regex_utils import regex_tree, join_with_or, iter_regex_tree_match_strings
from bench_convertisseur_xml.types import PageElementOrString

DATE_FORMAT = '%Y-%m-%d'

MONTH_NAMES = list(calendar.month_name)


DATE_NODE = regex_tree.Group(
    regex_tree.Sequence([
        regex_tree.Branching([
            r'(((?P<day_first>1er)|(?P<day>\d{1,2})) (?P<month_name>' + join_with_or(MONTH_NAMES[1:]) + r') ((?P<year>\d{4})|(?P<year_2digits>\d{2})))',
            r'((?P<day>\d{2})/(?P<month>\d{2})/((?P<year>\d{4})|(?P<year_2digits>\d{2})))',
        ]),
        # Check that the date string is followed by a valid separator
        # so that we don't match strings like 54/67/1980/A.
        r'(?=\s|\.|$|,|\)|;)',
    ]),
    group_name='__date',
)


def _handle_date_match_dict(match_dict: regex_tree.MatchDict) -> date:
    if match_dict.get('month_name'):
        match_month = match_dict['month_name'].lower()
        month = None
        for i, month_name in enumerate(MONTH_NAMES):
            if month_name.startswith(match_month):
                month = i
        if month is None:
            raise RuntimeError(f'couldnt find month for "{match_month}"')
    elif match_dict.get('month'):
        month = int(match_dict['month'])
    else:
        raise RuntimeError(f'expected month')
    
    if match_dict.get('day_first'):
        day = 1
    elif match_dict.get('day'):
        day = int(match_dict['day'])
    else:
        raise RuntimeError(f'expected day')

    if match_dict.get('year_2digits'):
        year_2digits = int(match_dict['year_2digits'])
        year = year_2digits + (1900 if year_2digits > (date.today().year - 2000 + 5) else 2000)
    elif match_dict.get('year'):
        year = int(match_dict['year'])
    else:
        raise RuntimeError(f'expected year')

    return date(
        day=day,
        month=month,
        year=year,
    )


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
    date_container['datetime'] = render_date_str(date_object)
    return date_container