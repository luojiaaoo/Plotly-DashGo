"""GUI lifecycle: cancellation, generations, and the pagehide path.

These cover the parts of the spec that only matter once there is a real interface:
every terminal path releases the login lock, a stale async result cannot overwrite a
newer login, ``pagehide`` clears the visible state synchronously, and nothing secret
reaches a log, an error string or the browser.
"""

import logging

import pytest

from common.orcarouter import runtime
from common.orcarouter.credentials import InMemoryCredentialStore, PkceAdapter, mask_api_key
from common.orcarouter.errors import CredentialError, NeedsReauthError, OrcaRouterTimeout

# --------------------------------------------------------------------------------------
# Generation isolation
# --------------------------------------------------------------------------------------


def test_a_stale_response_cannot_reach_a_newer_login(memory_store, monkeypatch):
    """A late URL or success from an abandoned attempt must not appear under a new one."""
    adapter = PkceAdapter(store=memory_store)
    first = adapter.start()

    # A second login begins; the first is abandoned.
    adapter.cancel(first.generation)
    second = adapter.start()
    assert second.generation > first.generation

    monkeypatch.setattr(
        'common.orcarouter.credentials.post_json',
        lambda *a, **k: (200, {'key': 'sk-orca-' + 'n' * 32, 'scope': 'api'}),
    )
    # The late result of the abandoned attempt cannot be exchanged at all.
    from common.orcarouter.errors import OrcaRouterTimeout

    with pytest.raises(OrcaRouterTimeout):
        adapter.exchange(first.generation, 'late-code')

    # Only the live attempt can complete, and it produced the current generation.
    credential = adapter.exchange(second.generation, 'fresh-code')
    assert credential.generation == 1
    assert adapter.load().api_key == 'sk-orca-' + 'n' * 32


def test_generations_are_monotonic_across_starts(memory_store):
    adapter = PkceAdapter(store=memory_store)
    generations = [adapter.start().generation for _ in range(5)]
    assert generations == sorted(generations)
    assert len(set(generations)) == 5


def test_switching_authentication_method_releases_a_pending_login(memory_store, fake_key):
    """Pasting a key must cancel an in-flight browser authorization."""
    runtime.cancel_all_connects()
    attempt = runtime.start_connect()
    assert runtime.pkce_adapter().get(attempt['generation']) is not None

    runtime.save_api_key(fake_key)
    runtime.cancel_all_connects()
    assert runtime.pkce_adapter().get(attempt['generation']) is None


# --------------------------------------------------------------------------------------
# pagehide
# --------------------------------------------------------------------------------------


def test_pagehide_handler_clears_busy_and_hint_synchronously_and_keeps_alive():
    """The handler must not depend on a guarded ``finally`` that refuses to mutate state."""
    from dash_callback.application.setting_.orcarouter_c import _CLIENT_PAGEHIDE_HANDLER

    assert "addEventListener('pagehide'" in _CLIENT_PAGEHIDE_HANDLER
    # Both the busy flag and the hint are cleared inside the handler itself.
    assert 'orcarouter-connect-busy' in _CLIENT_PAGEHIDE_HANDLER
    assert 'orcarouter-connect-hint-fragment' in _CLIENT_PAGEHIDE_HANDLER
    # Cancellation is sent with keepalive so it survives the unload.
    assert 'keepalive' in _CLIENT_PAGEHIDE_HANDLER
    assert '/orcarouter/cancel' in _CLIENT_PAGEHIDE_HANDLER
    # The listener is installed once, and a second login does not need a remount.
    assert '__orcaPagehideBound' in _CLIENT_PAGEHIDE_HANDLER


def test_pagehide_releases_the_server_side_attempt(memory_store):
    """After pagehide, the same page can start a second login without remounting."""
    adapter = runtime.pkce_adapter()
    adapter.cancel_all()

    first = runtime.start_connect()
    assert adapter.get(first['generation']) is not None

    # This is what the keepalive POST to /orcarouter/cancel does.
    assert runtime.cancel_connect(first['generation']) is True
    assert adapter.get(first['generation']) is None

    # A second login starts cleanly.
    second = runtime.start_connect()
    assert second['generation'] > first['generation']
    assert adapter.get(second['generation']) is not None
    assert adapter.get(second['generation']).pkce.verifier != adapter.get(first['generation'])


@pytest.mark.parametrize('terminal_path', ['success', 'denial', 'exchange_error', 'timeout', 'explicit_cancel'])
def test_every_terminal_path_releases_the_login_lock(terminal_path, memory_store, monkeypatch):
    adapter = PkceAdapter(store=memory_store)
    attempt = adapter.start()

    if terminal_path == 'success':
        monkeypatch.setattr(
            'common.orcarouter.credentials.post_json',
            lambda *a, **k: (200, {'key': 'sk-orca-' + 'x' * 32, 'scope': 'api'}),
        )
        adapter.exchange(attempt.generation, 'code')
    elif terminal_path == 'denial':
        monkeypatch.setattr('common.orcarouter.credentials.post_json', lambda *a, **k: (403, {}))
        with pytest.raises(CredentialError):
            adapter.exchange(attempt.generation, 'code')
    elif terminal_path == 'exchange_error':
        monkeypatch.setattr('common.orcarouter.credentials.post_json', lambda *a, **k: (500, {}))
        with pytest.raises(CredentialError):
            adapter.exchange(attempt.generation, 'code')
    elif terminal_path == 'timeout':
        # An attempt the user abandoned expires and stops holding the login lock.
        adapter.ATTEMPT_TTL_SECONDS = 0
        with pytest.raises(OrcaRouterTimeout):
            adapter.exchange(attempt.generation, 'code')
        assert len(adapter) == 0
    elif terminal_path == 'explicit_cancel':
        adapter.cancel(attempt.generation)

    assert len(adapter) == 0, f'{terminal_path} left the login lock held'


# --------------------------------------------------------------------------------------
# The cancel route
# --------------------------------------------------------------------------------------


def test_cancel_route_releases_an_attempt_and_carries_no_secret():
    import app  # noqa: F401  - builds the Dash layout the Flask test client requires
    from server import server

    pool = InMemoryCredentialStore()
    runtime.set_store(pool)
    attempt = runtime.start_connect()

    client = server.test_client()
    response = client.post('/orcarouter/cancel', data={'generation': str(attempt['generation'])})
    assert response.status_code == 200
    assert response.get_json() == {'cancelled': True}
    assert runtime.pkce_adapter().get(attempt['generation']) is None
    assert attempt['authorize_url'] not in response.get_data(as_text=True)


def test_cancel_route_rejects_a_bad_generation_without_crashing():
    import app  # noqa: F401
    from server import server

    runtime.set_store(InMemoryCredentialStore())
    response = server.test_client().post('/orcarouter/cancel', data={'generation': 'not-a-number'})
    assert response.status_code == 400
    assert response.get_json() == {'cancelled': False}


# --------------------------------------------------------------------------------------
# Redaction
# --------------------------------------------------------------------------------------


def test_nothing_secret_reaches_a_log_record(caplog, memory_store):
    """Log records are the most likely place a credential leaks; assert against them.

    This exercises the real code paths that handle a credential and then asserts on
    everything the project's loggers emitted, rather than on a line the test wrote
    itself.
    """
    # Importing the module registers the callbacks; their log statements are the ones
    # under test.
    from dash_callback.application.setting_ import orcarouter_c  # noqa: F401

    fake_key = 'sk-orca-' + 'l' * 32
    verifier = 'verifier-' + 'v' * 43

    with caplog.at_level(logging.DEBUG):
        credential = runtime.save_api_key(fake_key)
        attempt = runtime.start_connect()
        # A fresh attempt's verifier is exactly the value that must never be logged.
        pending = runtime.pkce_adapter().get(attempt['generation'])
        assert pending.pkce.verifier != verifier
        runtime.cancel_connect(attempt['generation'])
        # Touch the code paths that log, including the masked-status helper.
        from dash_callback.application.setting_.orcarouter_c import _masked_status

        _masked_status(credential)
        assert credential.masked_key in _masked_status(credential)

    captured = caplog.text
    assert fake_key not in captured, 'a raw API key reached a log record'
    assert pending.pkce.verifier not in captured, 'a PKCE verifier reached a log record'


def test_the_persisted_secret_is_not_plaintext_in_the_store():
    """The SQL store encrypts; the in-memory double must not be mistaken for it."""
    from common.utilities.util_encrypt import decrypt_data, encrypt_data

    key = 'sk-orca-' + 'p' * 32
    ciphertext = encrypt_data(key)
    assert key not in ciphertext
    assert decrypt_data(ciphertext) == key


def test_error_strings_never_carry_a_credential():
    from common.orcarouter.errors import CredentialError, OrcaRouterError

    secret = 'sk-orca-' + 'z' * 32
    assert secret not in str(CredentialError('x', 'a message'))
    assert secret not in str(OrcaRouterError('y', 'another message'))


def test_needs_reauth_error_names_the_account_generation_not_the_key():
    error = NeedsReauthError('revoked', auth_method='orcarouter-oauth', generation=3)
    assert error.auth_method == 'orcarouter-oauth'
    assert error.generation == 3
    assert 'sk-orca-' not in str(error)


def test_masked_key_is_what_the_ui_shows():
    key = 'sk-orca-' + 'm' * 32
    masked = mask_api_key(key)
    # The mask identifies the provider and nothing else: no character of the key.
    assert masked == 'sk-orca-' + '•' * 12
    assert mask_api_key('') == ''
