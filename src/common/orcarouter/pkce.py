"""PKCE primitives and the OAuth 2.0 authorization-code exchange.

Everything here is standard library only — no new dependency is needed for SHA-256
or base64url.

The verifier is generated fresh from ``secrets`` for every attempt, is never placed
in a URL, and never appears in a log line, an error message or a returned value that
is not the exchange request body itself.
"""

import base64
import hashlib
import hmac
import secrets
from urllib.parse import urlencode

from .errors import CredentialError
from .origins import authorize_url, validate_callback_url

#: Flow A — the code comes back to a loopback listener.
FLOW_LOOPBACK = 'loopback'
#: Flow B — the consent screen shows a code the user pastes back.
FLOW_OUT_OF_BAND = 'oob'
#: The literal ``callback_url`` value that selects Flow B.
OOB_CALLBACK_URL = 'oob'

#: Always S256. ``plain`` is never offered: the user can choose "Show me a code" on
#: the consent screen even in Flow A, which puts the challenge in human hands.
CODE_CHALLENGE_METHOD = 'S256'

#: The only scope this integration accepts. The response reports what was *granted*,
#: which is not necessarily what was asked for.
ACCEPTED_SCOPES = frozenset({'api'})

VERIFIER_BYTES = 32
STATE_BYTES = 16

DEFAULT_APP_NAME = 'DashGo'


def b64url(raw: bytes) -> str:
    """base64url without padding, per RFC 7636."""
    return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')


def new_verifier() -> str:
    """A fresh high-entropy verifier from the operating system CSPRNG."""
    return b64url(secrets.token_bytes(VERIFIER_BYTES))


def new_state() -> str:
    """A fresh opaque CSRF token from the operating system CSPRNG."""
    return b64url(secrets.token_bytes(STATE_BYTES))


def code_challenge(verifier: str) -> str:
    """``base64url(sha256(verifier))`` without padding."""
    if not verifier:
        raise ValueError('verifier must not be empty')
    return b64url(hashlib.sha256(verifier.encode('ascii')).digest())


def state_matches(expected: str, received: str) -> bool:
    """Constant-time state comparison for the Flow A callback."""
    if not expected or not received:
        return False
    return hmac.compare_digest(str(expected), str(received))


class PkceAttempt:
    """One authorization attempt. A new one is built for every attempt, always.

    The verifier only leaves this object inside :meth:`exchange_body`, which is the
    single place it is allowed to appear.
    """

    __slots__ = ('app_name', 'callback_url', 'flow', 'scope', 'state', 'verifier')

    def __init__(self, *, flow: str, callback_url: str, app_name: str = DEFAULT_APP_NAME, scope: str = 'api'):
        if flow not in (FLOW_LOOPBACK, FLOW_OUT_OF_BAND):
            raise ValueError(f'unknown flow {flow!r}')
        if scope not in ACCEPTED_SCOPES:
            raise ValueError(f'unsupported scope {scope!r}')
        self.flow = flow
        self.callback_url = validate_callback_url(callback_url) if flow == FLOW_LOOPBACK else OOB_CALLBACK_URL
        self.app_name = app_name
        self.scope = scope
        self.verifier = new_verifier()
        self.state = new_state()

    def challenge(self) -> str:
        return code_challenge(self.verifier)

    def build_authorize_url(self, auth_base: str) -> str:
        """The consent-screen URL. Carries the challenge, never the verifier."""
        query = urlencode(
            {
                'callback_url': self.callback_url,
                'code_challenge': self.challenge(),
                'code_challenge_method': CODE_CHALLENGE_METHOD,
                'state': self.state,
                'app_name': self.app_name,
                'scope': self.scope,
            }
        )
        return f'{authorize_url(auth_base)}?{query}'

    def exchange_body(self, code: str) -> dict:
        """The only payload that carries the verifier."""
        if not code or not str(code).strip():
            raise CredentialError('missing_code', 'No authorization code was supplied')
        return {
            'code': str(code).strip(),
            'code_verifier': self.verifier,
            'code_challenge_method': CODE_CHALLENGE_METHOD,
        }

    def __repr__(self) -> str:  # pragma: no cover - defensive, keeps the verifier out
        return f'<PkceAttempt flow={self.flow} state={self.state[:6]}…>'


def parse_exchange_response(status_code: int, payload: dict) -> tuple[str, str, str]:
    """Turn an exchange response into ``(key, scope, user_id)``.

    Raises :class:`CredentialError` with a user-actionable message for the
    documented failure statuses. Response bodies are never echoed back verbatim, so
    a relay that reflects the request cannot leak the verifier or a key into the UI.
    """
    if status_code == 200:
        key = str((payload or {}).get('key') or '').strip()
        if not key:
            raise CredentialError('exchange_malformed', 'OrcaRouter returned no key')
        scope = str(payload.get('scope') or '').strip()
        if scope not in ACCEPTED_SCOPES:
            raise CredentialError(
                'scope_downgrade',
                f'OrcaRouter granted scope "{scope or "none"}", which is not enough for inference',
            )
        return key, scope, str(payload.get('user_id') or '')

    if status_code == 400:
        raise CredentialError(
            'exchange_rejected',
            'OrcaRouter rejected the code challenge method for this authorization',
        )
    if status_code == 403:
        raise CredentialError(
            'code_rejected',
            'The authorization code is unknown, expired, already used, or does not match this client',
        )
    if status_code == 429:
        raise CredentialError(
            'rate_limited',
            'Too many OrcaRouter authorizations were started for this account. Wait and retry, or paste an API key instead.',
        )
    raise CredentialError('exchange_failed', f'OrcaRouter denied the code exchange (HTTP {status_code})')
