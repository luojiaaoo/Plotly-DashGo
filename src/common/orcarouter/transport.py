"""HTTP transport for OrcaRouter inference and model discovery.

One place builds the ``Authorization: Bearer`` header, so the API key is handled
identically no matter which auth adapter produced it. Nothing in this module writes a
credential to a log, an exception message or a return value.
"""

from __future__ import annotations

import json
from typing import Optional

from .errors import CatalogError, NeedsReauthError, OrcaRouterError
from .origins import chat_completions_url, models_url

try:  # pragma: no cover - requests is already a transitive dependency of Dash
    import requests
except ImportError:  # pragma: no cover
    requests = None

DEFAULT_TIMEOUT_SECONDS = 30


def _session(session=None):
    if session is not None:
        return session
    if requests is None:  # pragma: no cover
        raise OrcaRouterError('transport_unavailable', 'The requests library is not installed')
    return requests


def _auth_headers(credential) -> dict:
    return {
        'Authorization': f'Bearer {credential.api_key}',
        'Content-Type': 'application/json',
    }


def _raise_for_status(status_code: int, credential, body: str = '') -> None:
    """Map relay failures onto terminal, user-actionable errors.

    A ``401`` means this exact credential generation was revoked or is otherwise
    unusable. It is never retried and never triggers a refresh: OrcaRouter issues
    durable API keys, so the only recovery is re-authorizing.
    """
    if 200 <= status_code < 300:
        return
    if status_code == 401:
        raise NeedsReauthError(
            'OrcaRouter rejected this credential. It may have been revoked — authorize again or paste a new API key.',
            auth_method=getattr(credential, 'auth_method', ''),
            generation=getattr(credential, 'generation', 0),
        )
    if status_code == 403:
        raise OrcaRouterError('forbidden', 'OrcaRouter refused this request (HTTP 403)')
    if status_code == 429:
        raise OrcaRouterError('rate_limited', 'OrcaRouter rate-limited this request (HTTP 429)', retryable=True)
    if status_code >= 500:
        raise OrcaRouterError('upstream_error', f'OrcaRouter is unavailable (HTTP {status_code})', retryable=True)
    raise OrcaRouterError('request_failed', f'OrcaRouter refused this request (HTTP {status_code})')


def fetch_models(credential, *, capability: Optional[str] = None, session=None, timeout: int = 10) -> list[dict]:
    """Fetch the live model catalog from the inference origin.

    Bounded in time, in bytes and in item count. Raises :class:`CatalogError` for
    anything that should make the caller fall back to the verified seed, and
    :class:`NeedsReauthError` when the credential itself was rejected — that one is
    never swallowed into a degraded catalog.
    """
    from .catalog import CATALOG_MAX_BYTES, parse_catalog

    http = _session(session)
    url = models_url(credential.api_base, capability)
    try:
        response = http.get(url, headers=_auth_headers(credential), timeout=timeout, stream=True)
    except Exception as exc:  # network failure: degrade, do not crash the page
        raise CatalogError(f'Could not reach the OrcaRouter model catalog: {type(exc).__name__}') from exc

    try:
        if response.status_code == 401:
            _raise_for_status(401, credential)
        if response.status_code != 200:
            raise CatalogError(f'OrcaRouter model catalog returned HTTP {response.status_code}')

        raw = response.raw.read(CATALOG_MAX_BYTES + 1, decode_content=True) if hasattr(response, 'raw') else response.content
        if raw is None:
            raise CatalogError('OrcaRouter model catalog returned an empty body')
        if len(raw) > CATALOG_MAX_BYTES:
            raise CatalogError('OrcaRouter model catalog response was too large')
        payload = json.loads(raw)
    except CatalogError:
        raise
    except NeedsReauthError:
        raise
    except Exception as exc:
        raise CatalogError(f'Could not parse the OrcaRouter model catalog: {type(exc).__name__}') from exc

    return parse_catalog(payload)


def chat_completion(credential, *, model: str, messages: list[dict], session=None, timeout: int = DEFAULT_TIMEOUT_SECONDS, **params) -> dict:
    """One OpenAI-wire-format chat completion against OrcaRouter.

    Returns the decoded JSON body. The credential is only ever placed in the
    ``Authorization`` header.
    """
    http = _session(session)
    body = {'model': model, 'messages': messages}
    body.update({k: v for k, v in params.items() if v is not None})
    try:
        response = http.post(
            chat_completions_url(credential.api_base),
            headers=_auth_headers(credential),
            json=body,
            timeout=timeout,
        )
    except NeedsReauthError:
        raise
    except Exception as exc:
        raise OrcaRouterError('network_error', f'Could not reach OrcaRouter: {type(exc).__name__}', retryable=True) from exc

    _raise_for_status(response.status_code, credential)
    try:
        return response.json()
    except Exception as exc:
        raise OrcaRouterError('malformed_response', 'OrcaRouter returned a response that was not JSON') from exc


def post_json(url: str, body: dict, *, session=None, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> tuple[int, dict]:
    """POST JSON to an auth endpoint and return ``(status_code, parsed_body)``.

    Deliberately returns the raw status instead of raising on 4xx: the PKCE
    exchange turns the documented statuses into specific user-facing messages.
    """
    http = _session(session)
    try:
        response = http.post(url, json=body, timeout=timeout)
    except Exception as exc:
        raise OrcaRouterError('network_error', f'Could not reach OrcaRouter: {type(exc).__name__}', retryable=True) from exc
    try:
        payload = response.json()
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    return response.status_code, payload
