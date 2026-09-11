"""The credential seam, and the two adapters that sit on it.

Getting an OrcaRouter credential has exactly two entry points:

* :class:`ApiKeyAdapter` — the user pastes an ``sk-orca-…`` key they already hold;
* :class:`PkceAdapter` — the user authorizes in a browser via OAuth 2.0 + PKCE.

They are adapters over one small interface, :class:`CredentialStore`, and both produce
the same :class:`OrcaCredential`. Provider requests, model discovery and every AI
entry point consume that type and never learn which adapter produced it.

Storage reuses the project's existing secret mechanism: the peewee table
``sys_orcarouter_credential``, encrypted with ``util_encrypt`` (AES-CBC under
``CommonConf.ENCRYPT_KEY``). No new secret store is introduced.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Optional

from . import AUTH_METHOD_API_KEY, AUTH_METHOD_PKCE
from .errors import CredentialError, NeedsReauthError, OrcaRouterTimeout
from .origins import resolve_api_base, resolve_auth_base
from .pkce import DEFAULT_APP_NAME, FLOW_LOOPBACK, FLOW_OUT_OF_BAND, PkceAttempt, parse_exchange_response
from .transport import post_json

#: Prefix of every OrcaRouter API key. A format check only — it is not proof that a
#: credential is valid, and nothing bills a request just to make a form look green.
KEY_PREFIX = 'sk-orca-'
MIN_KEY_LENGTH = len(KEY_PREFIX) + 16


#: What a stored key looks like on screen. Deliberately contains no character of the
#: real key, not even a trailing fragment: the masked value is rendered in the settings
#: UI and therefore ends up in screenshots, support tickets and screen shares.
MASK_PLACEHOLDER = '•' * 12


def mask_api_key(api_key: str) -> str:
    """Render a key for display. Returns no part of the key itself."""
    if not api_key:
        return ''
    return f'{KEY_PREFIX}{MASK_PLACEHOLDER}' if api_key.startswith(KEY_PREFIX) else MASK_PLACEHOLDER


def looks_like_api_key(api_key: str) -> bool:
    return bool(api_key) and api_key.startswith(KEY_PREFIX) and len(api_key) >= MIN_KEY_LENGTH


@dataclass(frozen=True)
class OrcaCredential:
    """A usable OrcaRouter credential.

    This is what both adapters return and the only thing the rest of the application
    ever handles. ``api_key`` is deliberately excluded from :meth:`__repr__` so an
    accidental log of a credential object cannot leak it.
    """

    api_key: str
    auth_method: str
    auth_base: str
    api_base: str
    scope: str = 'api'
    user_id: str = ''
    generation: int = 1
    needs_reauth: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def masked_key(self) -> str:
        return mask_api_key(self.api_key)

    def describe(self) -> dict:
        """Everything the UI may show about this credential. No secret."""
        return {
            'auth_method': self.auth_method,
            'masked_key': self.masked_key,
            'scope': self.scope,
            'user_id': self.user_id,
            'generation': self.generation,
            'needs_reauth': self.needs_reauth,
            'api_base': self.api_base,
            'auth_base': self.auth_base,
        }

    def __repr__(self) -> str:  # pragma: no cover - defensive
        return f'OrcaCredential(auth_method={self.auth_method!r}, key={self.masked_key!r}, generation={self.generation})'


class CredentialStore:
    """The seam. Implementations decide *where* a credential lives, not *how* it is used."""

    def load(self, auth_method: str) -> Optional[OrcaCredential]:
        raise NotImplementedError

    def save(self, auth_method: str, api_key: str, *, scope: str = 'api', user_id: str = '') -> OrcaCredential:
        raise NotImplementedError

    def clear(self, auth_method: str) -> bool:
        raise NotImplementedError

    def mark_needs_reauth(self, auth_method: str, generation: int) -> bool:
        raise NotImplementedError

    def load_any(self) -> Optional[OrcaCredential]:
        """Prefer a healthy credential, falling back to one that needs re-authorization."""
        for auth_method in (AUTH_METHOD_PKCE, AUTH_METHOD_API_KEY):
            credential = self.load(auth_method)
            if credential and not credential.needs_reauth:
                return credential
        for auth_method in (AUTH_METHOD_PKCE, AUTH_METHOD_API_KEY):
            credential = self.load(auth_method)
            if credential:
                return credential
        return None


class SqlCredentialStore(CredentialStore):
    """Credential store backed by the project's existing database + encryption helper."""

    def load(self, auth_method: str) -> Optional[OrcaCredential]:
        from common.utilities.util_encrypt import decrypt_data
        from database.sql_db.dao import dao_orcarouter

        row = dao_orcarouter.get_credential(auth_method)
        if row is None:
            return None
        try:
            api_key = decrypt_data(row.api_key_encrypted)
        except Exception as exc:
            # A credential we cannot decrypt is unusable, and re-authorizing is the
            # only recovery. It is reported as such rather than silently dropped.
            raise NeedsReauthError(
                'The stored OrcaRouter credential could not be read and must be replaced',
                auth_method=auth_method,
                generation=row.generation,
            ) from exc
        return OrcaCredential(
            api_key=api_key,
            auth_method=row.auth_method,
            auth_base=resolve_auth_base(),
            api_base=resolve_api_base(),
            scope=row.scope or 'api',
            user_id=row.user_id or '',
            generation=row.generation,
            needs_reauth=bool(row.needs_reauth),
            created_at=row.update_datetime or datetime.now(),
        )

    def save(self, auth_method: str, api_key: str, *, scope: str = 'api', user_id: str = '') -> OrcaCredential:
        from common.utilities.util_encrypt import encrypt_data
        from database.sql_db.dao import dao_orcarouter

        if not looks_like_api_key(api_key):
            raise CredentialError(
                'invalid_key_format',
                f'An OrcaRouter API key starts with "{KEY_PREFIX}". Check the value and try again.',
            )
        if not dao_orcarouter.upsert_credential(
            auth_method=auth_method,
            api_key_encrypted=encrypt_data(api_key),
            scope=scope,
            user_id=user_id,
            needs_reauth=False,
        ):
            raise CredentialError('store_failed', 'Could not store the OrcaRouter credential')
        stored = self.load(auth_method)
        if stored is None:  # pragma: no cover - defensive
            raise CredentialError('store_failed', 'Could not read back the stored OrcaRouter credential')
        return stored

    def clear(self, auth_method: str) -> bool:
        from database.sql_db.dao import dao_orcarouter

        return dao_orcarouter.delete_credential(auth_method)

    def mark_needs_reauth(self, auth_method: str, generation: int) -> bool:
        from database.sql_db.dao import dao_orcarouter

        return dao_orcarouter.mark_needs_reauth(auth_method=auth_method, generation=generation)


class InMemoryCredentialStore(CredentialStore):
    """Non-persistent store, for tests and for callers that supply their own secret handling."""

    def __init__(self):
        self._rows: dict[str, dict] = {}
        self._lock = threading.Lock()

    def load(self, auth_method: str) -> Optional[OrcaCredential]:
        with self._lock:
            row = self._rows.get(auth_method)
            if row is None:
                return None
            return OrcaCredential(
                api_key=row['api_key'],
                auth_method=auth_method,
                auth_base=resolve_auth_base(),
                api_base=resolve_api_base(),
                scope=row.get('scope', 'api'),
                user_id=row.get('user_id', ''),
                generation=row.get('generation', 1),
                needs_reauth=row.get('needs_reauth', False),
            )

    def save(self, auth_method: str, api_key: str, *, scope: str = 'api', user_id: str = '') -> OrcaCredential:
        if not looks_like_api_key(api_key):
            raise CredentialError(
                'invalid_key_format',
                f'An OrcaRouter API key starts with "{KEY_PREFIX}". Check the value and try again.',
            )
        with self._lock:
            previous = self._rows.get(auth_method) or {}
            self._rows[auth_method] = {
                'api_key': api_key,
                'scope': scope,
                'user_id': user_id,
                'generation': previous.get('generation', 0) + 1,
                'needs_reauth': False,
            }
        return self.load(auth_method)

    def clear(self, auth_method: str) -> bool:
        with self._lock:
            return self._rows.pop(auth_method, None) is not None

    def mark_needs_reauth(self, auth_method: str, generation: int) -> bool:
        with self._lock:
            row = self._rows.get(auth_method)
            if row is None or row.get('generation') != generation:
                return False
            row['needs_reauth'] = True
            return True


@dataclass
class ApiKeyAdapter:
    """The "I already have a key" adapter."""

    store: CredentialStore
    auth_method: str = AUTH_METHOD_API_KEY

    def save(self, api_key: str) -> OrcaCredential:
        return self.store.save(self.auth_method, (api_key or '').strip())

    def load(self) -> Optional[OrcaCredential]:
        return self.store.load(self.auth_method)

    def clear(self) -> bool:
        return self.store.clear(self.auth_method)

    def status(self) -> Optional[dict]:
        credential = self.load()
        return credential.describe() if credential else None


# --------------------------------------------------------------------------------------
# PKCE adapter
# --------------------------------------------------------------------------------------


@dataclass
class PendingAttempt:
    """A single in-flight authorization.

    ``port`` is set only for Flow A. The verifier lives on ``pkce`` and is never
    serialised into UI state.
    """

    pkce: PkceAttempt
    generation: int
    authorize_url: str
    port: Optional[int] = None
    flow: str = FLOW_OUT_OF_BAND
    created_at: datetime = field(default_factory=datetime.now)
    cancelled: bool = False

    def is_expired(self, ttl_seconds: int, *, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now()
        return (now - self.created_at).total_seconds() > ttl_seconds

    def public(self) -> dict:
        """What may be sent to the browser: no verifier, no state-dependent secret."""
        return {
            'flow': self.flow,
            'authorize_url': self.authorize_url,
            'generation': self.generation,
            'port': self.port,
        }


class PkceAdapter:
    """The "sign in with OrcaRouter" adapter.

    Flow B (out-of-band code) is the default because DashGo is self-hosted software
    whose address differs on every deployment, so there is no callback address to
    predict. Flow A (loopback redirect) is available when the browser runs on the same
    machine as DashGo.
    """

    #: A pending attempt is abandoned after this long, mirroring the 10 minute TTL of
    #: an OrcaRouter authorization code. It bounds the login lock: an attempt the user
    #: simply walked away from cannot keep the next login blocked forever.
    ATTEMPT_TTL_SECONDS = 600

    def __init__(self, store: CredentialStore, *, auth_method: str = AUTH_METHOD_PKCE, app_name: str = DEFAULT_APP_NAME, session=None):
        self.store = store
        self.auth_method = auth_method
        self.app_name = app_name
        self._session = session
        self._lock = threading.Lock()
        self._pending: dict[int, PendingAttempt] = {}
        self._generation = 0

    # -- attempt lifecycle ----------------------------------------------------------

    def start(self, *, flow: str = FLOW_OUT_OF_BAND, callback_url: str = 'oob') -> PendingAttempt:
        """Begin an authorization attempt. A fresh verifier and state are generated here."""
        auth_base = resolve_auth_base()
        with self._lock:
            self._prune_expired_locked()
            self._generation += 1
            generation = self._generation
        pkce = PkceAttempt(flow=flow, callback_url=callback_url, app_name=self.app_name)
        port = None
        if flow == FLOW_LOOPBACK:
            from urllib.parse import urlsplit

            port = urlsplit(pkce.callback_url).port
        attempt = PendingAttempt(
            pkce=pkce,
            generation=generation,
            authorize_url=pkce.build_authorize_url(auth_base),
            port=port,
            flow=flow,
        )
        with self._lock:
            self._pending[generation] = attempt
        return attempt

    def _prune_expired_locked(self) -> int:
        expired = [g for g, attempt in self._pending.items() if attempt.is_expired(self.ATTEMPT_TTL_SECONDS)]
        for generation in expired:
            self._pending[generation].cancelled = True
            del self._pending[generation]
        return len(expired)

    def prune_expired(self) -> int:
        with self._lock:
            return self._prune_expired_locked()

    def get(self, generation: int) -> Optional[PendingAttempt]:
        with self._lock:
            self._prune_expired_locked()
            return self._pending.get(generation)

    def cancel(self, generation: int) -> bool:
        """Release one attempt. Safe to call for an attempt that already finished."""
        with self._lock:
            attempt = self._pending.pop(generation, None)
            if attempt is None:
                return False
            attempt.cancelled = True
        return True

    def cancel_all(self) -> int:
        with self._lock:
            for attempt in self._pending.values():
                attempt.cancelled = True
            count = len(self._pending)
            self._pending.clear()
        return count

    def __len__(self) -> int:
        with self._lock:
            return len(self._pending)

    # -- exchange -------------------------------------------------------------------

    def exchange(self, generation: int, code: str, *, state: Optional[str] = None) -> OrcaCredential:
        """Redeem an authorization code and persist the resulting API key.

        In Flow A the ``state`` echoed back through the browser is compared in
        constant time *before* the code is used. In Flow B there is no redirect, so a
        caller that supplies no state skips the comparison.
        """
        attempt = self.get(generation)
        if attempt is None:
            raise OrcaRouterTimeout('This OrcaRouter authorization is no longer active. Start again.')

        if attempt.pkce.flow == FLOW_LOOPBACK:
            from .pkce import state_matches

            if not state_matches(attempt.pkce.state, state or ''):
                self.cancel(generation)
                raise CredentialError('state_mismatch', 'The OrcaRouter callback state did not match this login. Start again.')

        auth_base = resolve_auth_base()
        from .origins import exchange_url

        try:
            status_code, payload = post_json(
                exchange_url(auth_base),
                attempt.pkce.exchange_body(code),
                session=self._session,
            )
        finally:
            # Single-use code, and this attempt is over either way. Releasing it here
            # is what stops a failed login from leaving the login lock held.
            self.cancel(generation)

        key, scope, user_id = parse_exchange_response(status_code, payload)
        credential = self.store.save(self.auth_method, key, scope=scope, user_id=user_id)
        return credential

    # -- status ---------------------------------------------------------------------

    def load(self) -> Optional[OrcaCredential]:
        return self.store.load(self.auth_method)

    def clear(self) -> bool:
        return self.store.clear(self.auth_method)

    def status(self) -> Optional[dict]:
        credential = self.load()
        return credential.describe() if credential else None


def ensure_credential_is_usable(credential: OrcaCredential, store: CredentialStore) -> OrcaCredential:
    """Guard used before a request. A revoked credential is terminal, never retried."""
    if credential.needs_reauth:
        raise NeedsReauthError(
            'This OrcaRouter credential was revoked and must be re-authorized',
            auth_method=credential.auth_method,
            generation=credential.generation,
        )
    return credential


def credential_after_401(credential: OrcaCredential, store: CredentialStore) -> OrcaCredential:
    """Mark the *exact* rejected generation and return the updated credential.

    Nothing is deleted: the old secret stays in place until a new login replaces it,
    so a transient upstream failure cannot cost the user their credential.
    """
    store.mark_needs_reauth(credential.auth_method, credential.generation)
    return replace(credential, needs_reauth=True)
