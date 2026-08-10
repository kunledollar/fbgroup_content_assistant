"""Optional OS keychain helpers. Environment variables remain the primary path."""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)
SERVICE = "CommunityPulseAI"


def load_secret(name: str, fallback: str | None = None) -> str | None:
    if fallback:
        return fallback
    try:
        import keyring

        value = keyring.get_password(SERVICE, name)
        return value or None
    except Exception:
        log.debug("keyring unavailable for %s", name, exc_info=True)
        return None


def store_secret(name: str, value: str) -> bool:
    try:
        import keyring

        keyring.set_password(SERVICE, name, value)
        return True
    except Exception:
        log.debug("keyring store failed for %s", name, exc_info=True)
        return False
