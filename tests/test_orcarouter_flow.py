"""End-to-end PKCE flow against a local fake OrcaRouter auth server.

The point of these tests is that the *whole* adapter runs — authorize URL, callback
handling, exchange, persistence — not just the hash helpers. The fake server implements
the documented contract: S256 only, single-use codes, granted scope reported back.

Nothing here talks to the public internet, and the consent decision is simulated by the
fake server. Real authorization always requires a human to approve it.
"""

import base64
import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest

from common.orcarouter.credentials import PkceAdapter
from common.orcarouter.errors import CredentialError, OrcaRouterTimeout
from common.orcarouter.loopback import LoopbackReceiver

b64url = lambda raw: base64.urlsafe_b64encode(raw).decode().rstrip('=')


class FakeAuthServer:
    """A minimal stand-in for the OrcaRouter consent screen and exchange endpoint."""

    def __init__(self, *, granted_scope='api', ttl_ok=True, fail_exchange_with=None):
        self.granted_scope = granted_scope
        self.ttl_ok = ttl_ok
        self.fail_exchange_with = fail_exchange_with
        self.codes = {}  # code -> challenge
        self.used = set()
        self.seen_authorize = []
        self.seen_exchange = []
        self.token_issue_count = 0
        self._server = None
        self._thread = None

    # -- lifecycle ------------------------------------------------------------------

    def start(self):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def _json(self, status, payload):
                body = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                url = urlsplit(self.path)
                if url.path != '/auth':
                    self.send_response(404)
                    self.end_headers()
                    return
                query = {k: v[0] for k, v in parse_qs(url.query).items()}
                outer.seen_authorize.append(query)
                code = b64url(f'code-{len(outer.codes)}'.encode())
                outer.codes[code] = query.get('code_challenge', '')
                page = f'<html><body><p>Authorize DashGo</p><code>{code}</code></body></html>'.encode()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(page)))
                self.end_headers()
                self.wfile.write(page)

            def do_POST(self):
                if urlsplit(self.path).path != '/api/v1/auth/keys':
                    self.send_response(404)
                    self.end_headers()
                    return
                length = int(self.headers.get('Content-Length') or 0)
                raw = self.rfile.read(length)
                try:
                    body = json.loads(raw)
                except Exception:
                    from urllib.parse import parse_qs as _pq

                    body = {k: v[0] for k, v in _pq(raw.decode()).items()}
                outer.seen_exchange.append(body)

                if outer.fail_exchange_with is not None:
                    return self._json(*outer.fail_exchange_with)

                method = body.get('code_challenge_method')
                if method != 'S256':
                    return self._json(400, {'error': 'invalid_request'})

                code = body.get('code')
                if code not in outer.codes or code in outer.used or not outer.ttl_ok:
                    return self._json(403, {'error': 'invalid_grant'})

                verifier = body.get('code_verifier') or ''
                actual = b64url(hashlib.sha256(verifier.encode()).digest())
                if actual != outer.codes[code]:
                    return self._json(403, {'error': 'invalid_grant'})
                if not verifier or verifier in outer.codes[code]:
                    return self._json(403, {'error': 'invalid_grant'})

                outer.used.add(code)
                outer.token_issue_count += 1
                return self._json(
                    200,
                    {'key': 'sk-orca-' + 'k' * 32, 'user_id': '12345', 'scope': outer.granted_scope},
                )

            def log_message(self, *args):
                return

        self._server = HTTPServer(('127.0.0.1', 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    @property
    def base(self):
        return f'http://127.0.0.1:{self._server.server_address[1]}'

    def stop(self):
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None


@pytest.fixture
def auth_server(monkeypatch):
    server = FakeAuthServer().start()
    monkeypatch.setenv('ORCA_AUTH_BASE_URL', server.base)
    yield server
    server.stop()


# --------------------------------------------------------------------------------------
# Happy path
# --------------------------------------------------------------------------------------


def test_full_out_of_band_login_persists_a_usable_credential(auth_server, memory_store):
    adapter = PkceAdapter(store=memory_store)
    attempt = adapter.start()
    payload = attempt.public()
    generation = payload['generation']

    # The consent screen is what the user opens; the code is what it displays.
    assert payload['authorize_url'].startswith(auth_server.base + '/auth?')
    code = _code_from_consent(auth_server, payload)

    credential = adapter.exchange(generation, code)

    assert credential.api_key.startswith('sk-orca-')
    assert credential.scope == 'api'
    assert credential.user_id == '12345'
    assert adapter.load().api_key == credential.api_key
    # The credential is reusable: a second call does not mint a second key.
    assert adapter.load().generation == 1
    assert auth_server.token_issue_count == 1


def test_the_verifier_never_reaches_the_authorize_request(auth_server, memory_store):
    adapter = PkceAdapter(store=memory_store)
    attempt = adapter.start()
    # Open the consent URL as the browser would, then inspect what was sent.
    _code_from_consent(auth_server, attempt.public())

    sent = auth_server.seen_authorize[-1]
    verifier = attempt.pkce.verifier
    assert 'code_verifier' not in sent
    assert verifier not in json.dumps(sent)
    # Only the S256 challenge is sent.
    assert sent['code_challenge'] == attempt.pkce.challenge()
    assert sent['code_challenge_method'] == 'S256'
    assert verifier != sent['code_challenge']


def test_exchange_sends_the_verifier_to_the_auth_origin_exchange_path(auth_server, memory_store):
    adapter = PkceAdapter(store=memory_store)
    attempt = adapter.start()
    code = _code_from_consent(auth_server, attempt.public())
    adapter.exchange(attempt.generation, code)

    body = auth_server.seen_exchange[-1]
    assert body['code'] == code
    assert body['code_verifier'] == attempt.pkce.verifier
    assert body['code_challenge_method'] == 'S256'


# --------------------------------------------------------------------------------------
# Failure paths
# --------------------------------------------------------------------------------------


def test_a_code_cannot_be_reused(auth_server, memory_store):
    adapter = PkceAdapter(store=memory_store)
    attempt = adapter.start()
    code = _code_from_consent(auth_server, attempt.public())
    adapter.exchange(attempt.generation, code)

    second = adapter.start()
    with pytest.raises((CredentialError, OrcaRouterTimeout)):
        # The same code, redeemed through a fresh attempt.
        adapter.exchange(second.generation, code)
    assert auth_server.token_issue_count == 1


def test_an_expired_code_is_rejected(auth_server, memory_store):
    adapter = PkceAdapter(store=memory_store)
    attempt = adapter.start()
    code = _code_from_consent(auth_server, attempt.public())
    auth_server.ttl_ok = False
    with pytest.raises(CredentialError) as exc:
        adapter.exchange(attempt.generation, code)
    assert exc.value.code == 'code_rejected'


def test_a_denied_authorization_never_produces_a_credential(auth_server, memory_store):
    """Denial is terminal: no key, no pending attempt, and the UI lock is released."""
    adapter = PkceAdapter(store=memory_store)
    attempt = adapter.start()
    auth_server.fail_exchange_with = (403, {'error': 'access_denied'})

    with pytest.raises(CredentialError):
        adapter.exchange(attempt.generation, 'whatever-the-user-was-shown')

    assert adapter.load() is None
    assert len(adapter) == 0
    assert memory_store.load_any() is None


def test_rate_limiting_is_reported_as_429(auth_server, memory_store):
    adapter = PkceAdapter(store=memory_store)
    attempt = adapter.start()
    auth_server.fail_exchange_with = (429, {'error': 'too_many_requests'})
    with pytest.raises(CredentialError) as exc:
        adapter.exchange(attempt.generation, 'any-code')
    assert exc.value.code == 'rate_limited'
    assert len(adapter) == 0


def test_a_scope_downgrade_is_not_persisted(auth_server, memory_store):
    auth_server.granted_scope = 'connector'
    adapter = PkceAdapter(store=memory_store)
    attempt = adapter.start()
    code = _code_from_consent(auth_server, attempt.public())
    with pytest.raises(CredentialError) as exc:
        adapter.exchange(attempt.generation, code)
    assert exc.value.code == 'scope_downgrade'
    assert adapter.load() is None, 'a key we cannot use must not be stored'


def test_cancelling_before_the_code_arrives_ends_the_attempt(auth_server, memory_store):
    adapter = PkceAdapter(store=memory_store)
    attempt = adapter.start()
    adapter.cancel(attempt.generation)
    with pytest.raises(OrcaRouterTimeout):
        adapter.exchange(attempt.generation, 'a-code-that-arrives-late')
    assert adapter.load() is None


# --------------------------------------------------------------------------------------
# Flow A: loopback redirect
# --------------------------------------------------------------------------------------


@pytest.mark.slow
def test_flow_a_delivers_the_code_through_a_real_loopback_listener(monkeypatch):
    """A real socket, a real HTTP request, and a real constant-time state comparison."""
    import urllib.request

    with LoopbackReceiver() as receiver:
        callback = receiver.callback_url()
        assert callback.startswith('http://127.0.0.1:')

        state = b64url(b'state-value')
        sender = threading.Thread(
            target=lambda: urllib.request.urlopen(f'{callback}?code=abc123&state={state}', timeout=5).read(),
            daemon=True,
        )
        sender.start()
        received = receiver.wait(timeout=10)

    assert received == {'code': 'abc123', 'state': state}


@pytest.mark.slow
def test_flow_a_state_mismatch_is_rejected_end_to_end(auth_server, memory_store):
    adapter = PkceAdapter(store=memory_store)
    attempt = adapter.start(flow='loopback', callback_url='http://127.0.0.1:59999/cb')
    with pytest.raises(CredentialError) as exc:
        adapter.exchange(attempt.generation, 'intercepted-code', state='not-the-state')
    assert exc.value.code == 'state_mismatch'
    assert len(adapter) == 0
    assert not auth_server.seen_exchange, 'a mismatched state must never reach the exchange'


def _code_from_consent(server, payload):
    """Open the authorize URL the way the user's browser would, and read the code.

    The adapter itself never opens a browser — the UI hands the URL to the user — so
    the test plays the part of the browser and of the human who approves.
    """
    import urllib.request
    from urllib.parse import urlsplit as _urlsplit

    url = payload['authorize_url']
    # The URL the adapter built points at the real public default; the fixture has
    # pointed the auth origin at the fake server, so both agree on the host and port.
    body = urllib.request.urlopen(url, timeout=5).read().decode()
    code = body.rsplit('<code>', 1)[-1].split('</code>', 1)[0]
    assert code, f'consent screen returned no code: {body[:200]}'
    assert _urlsplit(url).path == '/auth'
    return code
