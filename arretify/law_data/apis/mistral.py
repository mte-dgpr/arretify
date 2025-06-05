# TODO : group with eurlex and legifrance clients to a new folder
# containing all integrations with external APIs.
from dataclasses import replace as dataclass_replace

from arretify._vendor import mistralai

from arretify.types import SessionContext
from arretify.errors import SettingsError, DependencyError


def initialize_mistral_client(session_context: SessionContext) -> SessionContext:
    if not hasattr(mistralai, "Mistral"):
        raise DependencyError("Dependency mistralai seems to be missing")

    if not session_context.settings.mistral_api_key:
        raise SettingsError("MistralAI credentials are not provided")

    mistral_client = mistralai.Mistral(api_key=session_context.settings.mistral_api_key)
    return dataclass_replace(
        session_context,
        mistral_client=mistral_client,
    )
