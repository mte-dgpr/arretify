from typing import Literal

from clients_api_droit.eurlex import search_act


ActType = Literal['directive', 'regulation', 'decision']


def get_eu_act_url_with_year_and_num(act_type: ActType, year: int, number: int) -> str | None:
    for act in search_act(act_type, year, number):
        return act['url']
    return None