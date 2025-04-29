import os
from typing import Dict

from arretify.settings import Settings


_SETTINGS_ENV_MAP = {
    "tmp_dir": "TMP_DIR",
    "env": "ENV",
    "legifrance_client_id": "LEGIFRANCE_CLIENT_ID",
    "legifrance_client_secret": "LEGIFRANCE_CLIENT_SECRET",
    "eurlex_web_service_username": "EURLEX_WEB_SERVICE_USERNAME",
    "eurlex_web_service_password": "EURLEX_WEB_SERVICE_PASSWORD",
}


def load_settings_from_env(env_map: Dict[str, str] | None = None) -> Settings:
    """
    Load settings from environment variables.
    """
    if env_map is None:
        env_map = _SETTINGS_ENV_MAP

    # Remove keys with None values, so pydantic will use field defaults
    clean_values = {
        field: os.getenv(env_var)
        for field, env_var in env_map.items()
        if os.getenv(env_var) is not None
    }
    return Settings(**clean_values)
