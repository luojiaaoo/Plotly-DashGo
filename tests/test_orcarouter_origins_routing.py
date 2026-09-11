"""Origin routing: which host each request is allowed to reach.

The two public origins are unrelated, so these tests assert the actual URL each code
path builds, with the default configuration and with explicit overrides. They are the
automated counterpart of the manual "point auth and API at different origins" check.
"""

from common.orcarouter import origins, runtime
from common.orcarouter.credentials import InMemoryCredentialStore, PkceAdapter
from common.orcarouter.transport import chat_completion, fetch_models

PUBLIC_AUTH = 'https://www.orcarouter.ai'
PUBLIC_API = 'https://api.orcarouter.ai/v1'


class RecordingSession:
    """Captures every URL a code path asks for, and returns a valid-looking response."""

    def __init__(self, payload=None, status=200):
        self.urls = []
        self.headers = []
        self._payload = payload if payload is not None else {'data': []}
        self._status = status

    def _record(self, url, kwargs):
        self.urls.append(url)
        self.headers.append((kwargs.get('headers') or {}).get('Authorization', ''))

    class _Response:
        def __init__(self, payload, status):
            self._payload = payload
            self.status_code = status
            self.content = b'{}'

            class _Raw:
                def __init__(self, payload):
                    self._payload = payload

                def read(self, *args, **kwargs):
                    import json

                    return json.dumps(self._payload).encode()

            self.raw = _Raw(payload)

        def json(self):
            return self._payload

    def get(self, url, **kwargs):
        self._record(url, kwargs)
        return self._Response(self._payload, self._status)

    def post(self, url, **kwargs):
        self._record(url, kwargs)
        return self._Response(self._payload, self._status)


def _credential(api_base=PUBLIC_API, auth_base=PUBLIC_AUTH):
    from common.orcarouter.credentials import OrcaCredential

    return OrcaCredential(
        api_key='sk-orca-' + 'a' * 32,
        auth_method='orcarouter',
        auth_base=auth_base,
        api_base=api_base,
    )


# --------------------------------------------------------------------------------------
# Defaults
# --------------------------------------------------------------------------------------


def test_discovery_only_ever_touches_the_api_origin():
    session = RecordingSession()
    fetch_models(_credential(), capability='chat', session=session)
    assert session.urls == [f'{PUBLIC_API}/models?capability=chat']
    assert 'www.orcarouter.ai' not in session.urls[0]


def test_inference_only_ever_touches_the_api_origin():
    session = RecordingSession(payload={'choices': []})
    chat_completion(_credential(), model='openai/gpt-5.5', messages=[], session=session)
    assert session.urls == [f'{PUBLIC_API}/chat/completions']
    assert 'www.orcarouter.ai' not in session.urls[0]


def test_the_code_exchange_only_ever_touches_the_auth_origin(monkeypatch):
    """The exchange is an auth request; it must never be sent to the inference origin."""
    seen = {}
    adapter = PkceAdapter(store=InMemoryCredentialStore())

    def spy(url, body, **kwargs):
        seen['url'] = url
        seen['body'] = body
        return 200, {'key': 'sk-orca-' + 'k' * 32, 'scope': 'api'}

    monkeypatch.setattr('common.orcarouter.credentials.post_json', spy)
    attempt = adapter.start()
    adapter.exchange(attempt.generation, 'a-code')

    assert seen['url'] == f'{PUBLIC_AUTH}/api/v1/auth/keys'
    assert 'api.orcarouter.ai' not in seen['url']
    # The exact path matters. The relay's `/v1` prefix does not apply to auth endpoints:
    # `/v1/auth/keys` is a 404, and only `/api/v1/auth/keys` exists.
    from urllib.parse import urlsplit

    assert urlsplit(seen['url']).path == '/api/v1/auth/keys'


def test_the_authorize_url_only_ever_touches_the_auth_origin():
    attempt = PkceAdapter(store=InMemoryCredentialStore()).start()
    payload = attempt.public()
    assert payload['authorize_url'].startswith(f'{PUBLIC_AUTH}/auth?')
    assert 'api.orcarouter.ai' not in payload['authorize_url']


# --------------------------------------------------------------------------------------
# Explicit overrides
# --------------------------------------------------------------------------------------


def test_explicit_overrides_route_each_concern_separately(monkeypatch):
    monkeypatch.setenv('ORCA_AUTH_BASE_URL', 'https://auth.internal.example')
    monkeypatch.setenv('ORCA_API_BASE_URL', 'https://api.internal.example')

    session = RecordingSession()
    credential = _credential(api_base=origins.resolve_api_base(), auth_base=origins.resolve_auth_base())
    fetch_models(credential, session=session)
    assert session.urls == ['https://api.internal.example/v1/models']

    seen = {}

    def spy(url, body, **kwargs):
        seen['url'] = url
        return 200, {'key': 'sk-orca-' + 'k' * 32, 'scope': 'api'}

    adapter = PkceAdapter(store=InMemoryCredentialStore())
    monkeypatch.setattr('common.orcarouter.credentials.post_json', spy)
    attempt = adapter.start()
    assert attempt.public()['authorize_url'].startswith('https://auth.internal.example/auth?')
    adapter.exchange(attempt.generation, 'code')
    assert seen['url'] == 'https://auth.internal.example/api/v1/auth/keys'


def test_a_shared_self_hosted_base_serves_both_concerns(monkeypatch):
    monkeypatch.setenv('ORCA_BASE_URL', 'https://orca.internal.example')
    assert origins.resolve_auth_base() == 'https://orca.internal.example'
    assert origins.resolve_api_base() == 'https://orca.internal.example/v1'

    session = RecordingSession()
    credential = _credential(api_base=origins.resolve_api_base(), auth_base=origins.resolve_auth_base())
    fetch_models(credential, session=session)
    assert session.urls == ['https://orca.internal.example/v1/models']


def test_an_api_override_alone_does_not_move_the_auth_origin(monkeypatch):
    monkeypatch.setenv('ORCA_API_BASE_URL', 'https://api.internal.example')
    assert origins.resolve_auth_base() == PUBLIC_AUTH

    adapter = PkceAdapter(store=InMemoryCredentialStore())
    assert adapter.start().public()['authorize_url'].startswith(f'{PUBLIC_AUTH}/auth?')


# --------------------------------------------------------------------------------------
# The runtime facade routes through the resolved origins
# --------------------------------------------------------------------------------------


def test_runtime_discovery_uses_the_resolved_api_origin(monkeypatch):
    store = InMemoryCredentialStore()
    runtime.set_store(store)
    store.save('orcarouter', 'sk-orca-' + 'a' * 32)

    seen = {}
    monkeypatch.setattr(
        'common.orcarouter.transport.fetch_models',
        lambda credential, **kwargs: (seen.setdefault('base', credential.api_base), [])[1],
    )
    runtime.discover_model_options(capability='chat')
    assert seen['base'] == PUBLIC_API


def test_bearer_header_is_the_only_place_the_key_travels():
    key = 'sk-orca-' + 'a' * 32
    session = RecordingSession()
    fetch_models(_credential(), session=session)
    assert session.headers == [f'Bearer {key}']
    # The key is in the header and nowhere in the URL.
    assert key not in session.urls[0]
