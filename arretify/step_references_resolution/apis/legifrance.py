from typing import Dict
from datetime import date

# Load settings to be sure that we provide
# config to the legifrance package
from arretify._vendor.clients_api_droit.clients_api_droit.legifrance import (
    authenticate,
    search_arrete,
    search_decret,
    search_circulaire,
)

from arretify.utils.dev_cache import use_dev_cache


_TOKENS: Dict | None = None


@use_dev_cache
def get_arrete_legifrance_id(date: date, title: str) -> str | None:
    tokens = _get_tokens()
    for arrete in search_arrete(tokens, date, title):
        arrete_cid = arrete["titles"][0]["cid"]
        return arrete_cid
    return None


@use_dev_cache
def get_decret_legifrance_id(date: date, num: str | None, title: str | None) -> str | None:
    if not num and not title:
        raise ValueError("Either num or title must be provided")

    tokens = _get_tokens()
    for decret in search_decret(tokens, date, num=num, title=title):
        decret_cid = decret["titles"][0]["cid"]
        return decret_cid
    return None


@use_dev_cache
def get_circulaire_legifrance_id(date: date, title: str) -> str | None:
    tokens = _get_tokens()
    for circulaire in search_circulaire(tokens, date, title):
        circulaire_cid = circulaire["titles"][0]["cid"]
        return circulaire_cid
    return None


def _get_tokens():
    global _TOKENS
    if _TOKENS is None:
        _TOKENS = authenticate()
    return _TOKENS
