from datetime import date
from dataclasses import replace as dataclass_replace

from requests.exceptions import RequestException

from arretify._vendor.clients_api_droit.clients_api_droit.legifrance import (
    LegifranceClient,
    LegifranceSettings,
    authenticate,
    search_arrete,
    search_decret,
    search_circulaire,
)

from arretify.types import SessionContext
from arretify.utils.dev_cache import use_dev_cache
from arretify.errors import ErrorCodes, catch_and_convert_into_arretify_error, SettingsError


@catch_and_convert_into_arretify_error(RequestException, ErrorCodes.law_data_api_error)
def initialize_legifrance_client(session_context: SessionContext) -> SessionContext:
    if (
        not session_context.settings.legifrance_client_id
        or not session_context.settings.legifrance_client_secret
    ):
        raise SettingsError("Legifrance credentials are not provided")

    legifrance_settings = LegifranceSettings(
        client_id=session_context.settings.legifrance_client_id,
        client_secret=session_context.settings.legifrance_client_secret,
        tmp_dir=session_context.settings.tmp_dir,
    )
    legifrance_client = authenticate(LegifranceClient(settings=legifrance_settings))
    return dataclass_replace(
        session_context,
        legifrance_client=legifrance_client,
    )


@use_dev_cache
@catch_and_convert_into_arretify_error(RequestException, ErrorCodes.law_data_api_error)
def get_arrete_legifrance_id(session_context: SessionContext, date: date, title: str) -> str | None:
    legifrance_client = _assert_client_initialized(session_context)
    for arrete in search_arrete(legifrance_client, date, title):
        arrete_cid = arrete["titles"][0]["cid"]
        return arrete_cid
    return None


@use_dev_cache
@catch_and_convert_into_arretify_error(RequestException, ErrorCodes.law_data_api_error)
def get_decret_legifrance_id(
    session_context: SessionContext, date: date, num: str | None, title: str | None
) -> str | None:
    if not num and not title:
        raise ValueError("Either num or title must be provided")

    legifrance_client = _assert_client_initialized(session_context)
    for decret in search_decret(legifrance_client, date, num=num, title=title):
        decret_cid = decret["titles"][0]["cid"]
        return decret_cid
    return None


@use_dev_cache
@catch_and_convert_into_arretify_error(RequestException, ErrorCodes.law_data_api_error)
def get_circulaire_legifrance_id(
    session_context: SessionContext, date: date, title: str
) -> str | None:
    legifrance_client = _assert_client_initialized(session_context)
    for circulaire in search_circulaire(legifrance_client, date, title):
        circulaire_cid = circulaire["titles"][0]["cid"]
        return circulaire_cid
    return None


def _assert_client_initialized(session_context: SessionContext) -> LegifranceClient:
    if not session_context.legifrance_client:
        raise ValueError("Legifrance client is not initialized")
    return session_context.legifrance_client
