"""
_settings.py
Ian Kollipara <ian.kollipara@cune.edu>

This file contains the settings for the MeiliSearch Django app.
"""

from dataclasses import dataclass
from typing import TypedDict


class DjangoMeiliSettings(TypedDict):
    """
    Settings for the MeiliSearch Django app.

    Attributes:
        https: Whether to use HTTPS or not.
        host: The host for the MeiliSearch instance.
        master_key: The master key for the MeiliSearch instance.
        port: The port for the MeiliSearch instance.
    """

    HTTPS: bool
    HOST: str
    MASTER_KEY: str
    PORT: int
    TIMEOUT: int | None
    CLIENT_AGENTS: tuple[str] | None
    DEBUG: bool | None
    SYNC: bool | None
    OFFLINE: bool | None


@dataclass(frozen=True, slots=True)
class _DjangoMeiliSettings:
    """
    Settings for the MeiliSearch Django app.

    Attributes:
        https: Whether to use HTTPS or not.
        host: The host for the MeiliSearch instance.
        master_key: The master key for the MeiliSearch instance.
        port: The port for the MeiliSearch instance.
    """

    https: bool
    host: str
    master_key: str
    port: int
    timeout: int | None
    client_agents: tuple[str] | None
    debug: bool
    sync: bool
    offline: bool

    @classmethod
    def from_settings(cls) -> "_DjangoMeiliSettings":
        from django.conf import settings

        return cls(
            https=settings.MEILISEARCH.get("HTTPS", False),
            host=settings.MEILISEARCH.get("HOST", "localhost"),
            master_key=settings.MEILISEARCH.get("MASTER_KEY", None),
            port=settings.MEILISEARCH.get("PORT", 7700),
            timeout=settings.MEILISEARCH.get("TIMEOUT", None),
            client_agents=settings.MEILISEARCH.get("CLIENT_AGENTS", None),
            debug=settings.MEILISEARCH.get("DEBUG", settings.DEBUG),
            sync=settings.MEILISEARCH.get("SYNC", False),
            offline=settings.MEILISEARCH.get("OFFLINE", False),
        )
