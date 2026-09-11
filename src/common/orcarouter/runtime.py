"""The single facade every AI entry point and every settings screen talks to.

Nothing outside this package builds an ``Authorization`` header, resolves an origin,
or calls a catalog endpoint. That keeps the credential adapter, the transport and the
capability filter in one place instead of copied into each page.
"""

from __future__ import annotations

from typing import Iterable, Optional

from . import AUTH_METHOD_API_KEY, AUTH_METHOD_LABELS, AUTH_METHOD_PKCE
from .catalog import CAPABILITY_CHAT, ModelOption, list_model_options
from .credentials import (
    ApiKeyAdapter,
    CredentialStore,
    OrcaCredential,
    PkceAdapter,
    SqlCredentialStore,
    credential_after_401,
)
from .errors import NeedsReauthError
from .origins import resolve_api_base, resolve_auth_base
from .pkce import FLOW_LOOPBACK, FLOW_OUT_OF_BAND

_store: Optional[CredentialStore] = None
_pkce_adapter: Optional[PkceAdapter] = None


def get_store() -> CredentialStore:
    global _store
    if _store is None:
        _store = SqlCredentialStore()
    return _store


def set_store(store: Optional[CredentialStore]) -> None:
    """Swap the store. Used by tests and by embedders with their own secret handling."""
    global _store, _pkce_adapter
    _store = store
    _pkce_adapter = None


def api_key_adapter() -> ApiKeyAdapter:
    return ApiKeyAdapter(store=get_store())


def pkce_adapter() -> PkceAdapter:
    global _pkce_adapter
    if _pkce_adapter is None:
        _pkce_adapter = PkceAdapter(store=get_store())
    return _pkce_adapter


def current_credential() -> Optional[OrcaCredential]:
    """The credential inference should use, whichever adapter produced it."""
    return get_store().load_any()


def auth_status() -> dict:
    """Everything the settings screen needs. Contains no secret."""
    return {
        'auth_base': resolve_auth_base(),
        'api_base': resolve_api_base(),
        'api_key': api_key_adapter().status(),
        'pkce': pkce_adapter().status(),
        'methods': [
            {'id': AUTH_METHOD_API_KEY, 'label': AUTH_METHOD_LABELS[AUTH_METHOD_API_KEY]},
            {'id': AUTH_METHOD_PKCE, 'label': AUTH_METHOD_LABELS[AUTH_METHOD_PKCE]},
        ],
        'connected': current_credential() is not None,
    }


def save_api_key(api_key: str) -> OrcaCredential:
    return api_key_adapter().save(api_key)


def clear_api_key() -> bool:
    return api_key_adapter().clear()


def start_connect(flow: str = FLOW_OUT_OF_BAND, callback_url: str = 'oob') -> dict:
    """Begin a PKCE authorization and return what the UI may display."""
    attempt = pkce_adapter().start(flow=flow, callback_url=callback_url)
    payload = attempt.public()
    if flow == FLOW_LOOPBACK:
        payload['instructions'] = f'A browser window should open. If not, visit:\n{attempt.authorize_url}'
    else:
        payload['instructions'] = f'Open this URL, approve access, then paste the code shown on the page back here:\n{attempt.authorize_url}'
    return payload


def complete_connect(generation: int, code: str, state: Optional[str] = None) -> OrcaCredential:
    return pkce_adapter().exchange(generation, code, state=state)


def cancel_connect(generation: int) -> bool:
    return pkce_adapter().cancel(generation)


def cancel_all_connects() -> int:
    return pkce_adapter().cancel_all()


def discover_model_options(
    capability: str = CAPABILITY_CHAT,
    required_modalities: Iterable[str] = (),
    *,
    credential: Optional[OrcaCredential] = None,
) -> tuple[list[ModelOption], bool]:
    """Model options for one entry point, filtered by that entry point's capability.

    Returns ``(options, degraded)``. Raises :class:`NeedsReauthError` when the
    credential was rejected — a revoked key is a terminal state, not a catalog outage.
    """
    credential = credential or current_credential()
    if credential is None:
        return [], False
    if credential.needs_reauth:
        raise NeedsReauthError(
            'This OrcaRouter credential was revoked and must be re-authorized',
            auth_method=credential.auth_method,
            generation=credential.generation,
        )
    return list_model_options(credential, capability=capability, required_modalities=required_modalities)


def send_chat(credential: OrcaCredential, *, model: str, messages: list[dict], **params) -> dict:
    """Run one chat completion, moving the exact rejected generation to needs-reauth on 401."""
    from .transport import chat_completion

    try:
        return chat_completion(credential, model=model, messages=messages, **params)
    except NeedsReauthError:
        credential_after_401(credential, get_store())
        raise


__all__ = [
    'FLOW_LOOPBACK',
    'FLOW_OUT_OF_BAND',
    'api_key_adapter',
    'auth_status',
    'cancel_all_connects',
    'cancel_connect',
    'clear_api_key',
    'complete_connect',
    'current_credential',
    'discover_model_options',
    'get_store',
    'pkce_adapter',
    'save_api_key',
    'send_chat',
    'set_store',
    'start_connect',
]
