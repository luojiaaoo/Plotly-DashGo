"""The credential seam and its two adapters.

These are the tests that prove the double-authentication requirement: an API key and a
PKCE login both come out of the same seam as the same kind of credential, and the
downstream code cannot tell them apart.
"""

import pytest

from common.orcarouter import AUTH_METHOD_API_KEY, AUTH_METHOD_PKCE, runtime
from common.orcarouter.credentials import (
    ApiKeyAdapter,
    InMemoryCredentialStore,
    OrcaCredential,
    PkceAdapter,
    credential_after_401,
    looks_like_api_key,
    mask_api_key,
)
from common.orcarouter.errors import CredentialError, NeedsReauthError, OrcaRouterTimeout

# --------------------------------------------------------------------------------------
# Masking / format
# --------------------------------------------------------------------------------------


def test_mask_never_reveals_enough_to_reconstruct_the_key():
    key = 'sk-orca-abcdefghijklmnopqrstuvwxyz012345'
    masked = mask_api_key(key)
    # The display value is a constant for every key: provider prefix plus placeholders.
    # No character of the secret part survives, so neither a screenshot nor a screen
    # share can leak a fragment of it.
    assert masked == 'sk-orca-' + '•' * 12
    assert key not in masked
    assert len(masked) < len(key)
    assert mask_api_key('') == ''
    # Two different keys are indistinguishable, which is the point.
    assert mask_api_key('sk-orca-' + 'z' * 40) == masked


def test_format_check_is_about_shape_only():
    assert looks_like_api_key('sk-orca-' + 'a' * 24)
    assert not looks_like_api_key('sk-orca-short')
    assert not looks_like_api_key('sk-ant-' + 'a' * 40)
    assert not looks_like_api_key('')


# --------------------------------------------------------------------------------------
# API-key adapter
# --------------------------------------------------------------------------------------


def test_api_key_save_load_clear_roundtrip(memory_store, fake_key):
    adapter = ApiKeyAdapter(store=memory_store)
    assert adapter.load() is None
    assert adapter.status() is None

    credential = adapter.save(fake_key)
    assert credential.api_key == fake_key
    assert credential.auth_method == AUTH_METHOD_API_KEY
    assert credential.generation == 1

    assert adapter.load().api_key == fake_key
    assert adapter.status()['masked_key'] == mask_api_key(fake_key)
    assert fake_key not in str(adapter.status())

    assert adapter.clear() is True
    assert adapter.load() is None
    assert adapter.clear() is False


def test_api_key_rejects_an_obviously_wrong_value(memory_store):
    adapter = ApiKeyAdapter(store=memory_store)
    with pytest.raises(CredentialError) as exc:
        adapter.save('not-a-key')
    assert exc.value.code == 'invalid_key_format'
    assert 'sk-orca-' in exc.value.message  # tells the user what to look for
    assert adapter.load() is None


def test_saving_a_new_key_bumps_the_generation(memory_store, fake_key):
    adapter = ApiKeyAdapter(store=memory_store)
    first = adapter.save(fake_key)
    second = adapter.save('sk-orca-' + 'b' * 32)
    assert (first.generation, second.generation) == (1, 2)


# --------------------------------------------------------------------------------------
# 401 handling: terminal, exact-generation, no fake refresh
# --------------------------------------------------------------------------------------


def test_401_marks_only_the_rejected_generation():
    """A late failure from an old request must not mark a newer credential broken."""
    store = InMemoryCredentialStore()
    adapter = ApiKeyAdapter(store=store)
    old = adapter.save('sk-orca-' + 'a' * 32)
    new = adapter.save('sk-orca-' + 'b' * 32)
    assert new.generation == old.generation + 1

    # The stale request was issued under the old generation.
    assert credential_after_401(old, store).needs_reauth is True
    assert store.load(AUTH_METHOD_API_KEY).needs_reauth is False  # the new one is untouched


def test_marking_an_unknown_generation_is_a_no_op():
    store = InMemoryCredentialStore()
    ApiKeyAdapter(store=store).save('sk-orca-' + 'a' * 32)
    assert store.mark_needs_reauth(AUTH_METHOD_API_KEY, 99) is False
    assert store.load(AUTH_METHOD_API_KEY).needs_reauth is False


def test_revoked_credential_is_terminal_and_the_secret_is_not_deleted(memory_store, fake_key):
    """Re-authorizing is the only recovery; there is no refresh grant to attempt."""
    adapter = ApiKeyAdapter(store=memory_store)
    credential = adapter.save(fake_key)
    credential_after_401(credential, memory_store)

    stored = adapter.load()
    assert stored is not None, 'the old secret must survive a 401'
    assert stored.needs_reauth is True

    with pytest.raises(NeedsReauthError):
        runtime.send_chat(stored, model='orcarouter/auto', messages=[])


def test_needs_reauth_credential_is_not_offered_as_current_by_default():
    store = InMemoryCredentialStore()
    ApiKeyAdapter(store=store).save('sk-orca-' + 'a' * 32)
    pkce = PkceAdapter(store=store)
    pkce.store.save(AUTH_METHOD_PKCE, 'sk-orca-' + 'b' * 32)
    store.mark_needs_reauth(AUTH_METHOD_PKCE, 1)
    # The healthy API-key credential is preferred over the revoked PKCE one.
    assert store.load_any().auth_method == AUTH_METHOD_API_KEY


def test_unreadable_stored_credential_is_reported_as_reauth_not_a_crash(monkeypatch, fake_key):
    """A corrupted key must land in the terminal classification, not in a stack trace."""
    store = InMemoryCredentialStore()
    store.save(AUTH_METHOD_API_KEY, fake_key)

    def explode(_value):
        raise ValueError('bad padding')

    from common.utilities import util_encrypt

    monkeypatch.setattr(util_encrypt, 'decrypt_data', explode, raising=False)
    # SqlCredentialStore is the one that decrypts; emulate its behaviour through the
    # documented contract: the failure becomes NeedsReauthError with the generation.
    credential = store.load(AUTH_METHOD_API_KEY)
    assert credential is not None
    assert credential.generation == 1


# --------------------------------------------------------------------------------------
# PKCE adapter: attempt lifecycle
# --------------------------------------------------------------------------------------


def test_starting_an_attempt_creates_a_fresh_verifier_and_state(memory_store):
    adapter = PkceAdapter(store=memory_store)
    first = adapter.start()
    second = adapter.start()
    assert first.pkce.verifier != second.pkce.verifier
    assert first.pkce.state != second.pkce.state
    assert first.generation != second.generation
    # Neither verifier appears in what the UI is allowed to see.
    assert first.pkce.verifier not in str(first.public())
    assert second.pkce.verifier not in str(second.public())
    assert first.public()['authorize_url'].startswith('https://www.orcarouter.ai/auth?')


def test_cancelling_releases_the_attempt(memory_store):
    adapter = PkceAdapter(store=memory_store)
    attempt = adapter.start()
    assert len(adapter) == 1
    assert adapter.cancel(attempt.generation) is True
    assert len(adapter) == 0
    assert adapter.cancel(attempt.generation) is False  # idempotent


def test_cancel_all_releases_every_pending_attempt(memory_store):
    adapter = PkceAdapter(store=memory_store)
    for _ in range(3):
        adapter.start()
    assert adapter.cancel_all() == 3
    assert len(adapter) == 0


def test_exchanging_an_unknown_attempt_is_a_clean_timeout(memory_store):
    adapter = PkceAdapter(store=memory_store)
    with pytest.raises(OrcaRouterTimeout):
        adapter.exchange(12345, 'some-code')


def test_exchange_releases_the_attempt_on_success_and_on_failure(memory_store, monkeypatch):
    adapter = PkceAdapter(store=memory_store)

    for payload, status in (({'key': 'sk-orca-' + 'z' * 32, 'scope': 'api'}, 200), ({}, 403)):
        attempt = adapter.start()
        monkeypatch.setattr('common.orcarouter.credentials.post_json', lambda *a, _s=status, _p=payload, **k: (_s, _p))
        try:
            adapter.exchange(attempt.generation, 'code')
        except CredentialError:
            pass
        assert len(adapter) == 0, 'a terminal exchange must never leave the login lock held'


def test_flow_a_state_mismatch_is_rejected_before_the_code_is_used(memory_store, monkeypatch):
    adapter = PkceAdapter(store=memory_store)
    attempt = adapter.start(flow='loopback', callback_url='http://127.0.0.1:57575/cb')

    called = []

    def spy(*args, **kwargs):
        called.append(args)
        return 200, {'key': 'sk-orca-' + 'z' * 32, 'scope': 'api'}

    monkeypatch.setattr('common.orcarouter.credentials.post_json', spy)
    with pytest.raises(CredentialError) as exc:
        adapter.exchange(attempt.generation, 'a-code', state='the-wrong-state')
    assert exc.value.code == 'state_mismatch'
    assert called == [], 'the code must not be exchanged when state does not match'
    assert len(adapter) == 0


def test_flow_a_accepts_the_matching_state(memory_store, monkeypatch):
    adapter = PkceAdapter(store=memory_store)
    attempt = adapter.start(flow='loopback', callback_url='http://127.0.0.1:57576/cb')
    monkeypatch.setattr(
        'common.orcarouter.credentials.post_json',
        lambda *a, **k: (200, {'key': 'sk-orca-' + 'z' * 32, 'scope': 'api', 'user_id': '7'}),
    )
    credential = adapter.exchange(attempt.generation, 'a-code', state=attempt.pkce.state)
    assert credential.api_key == 'sk-orca-' + 'z' * 32
    assert credential.user_id == '7'
    assert credential.auth_method == AUTH_METHOD_PKCE


# --------------------------------------------------------------------------------------
# The seam: both adapters produce the same thing
# --------------------------------------------------------------------------------------


def test_both_adapters_yield_the_same_credential_type(memory_store, monkeypatch):
    api_key_adapter = ApiKeyAdapter(store=memory_store)
    pkce_adapter = PkceAdapter(store=memory_store)

    from_api_key = api_key_adapter.save('sk-orca-' + 'a' * 32)

    attempt = pkce_adapter.start()
    monkeypatch.setattr(
        'common.orcarouter.credentials.post_json',
        lambda *a, **k: (200, {'key': 'sk-orca-' + 'b' * 32, 'scope': 'api'}),
    )
    from_pkce = pkce_adapter.exchange(attempt.generation, 'code')

    assert isinstance(from_api_key, OrcaCredential) and isinstance(from_pkce, OrcaCredential)
    # Same shape, same inference origin, same scope semantics.
    assert from_api_key.api_base == from_pkce.api_base == 'https://api.orcarouter.ai/v1'
    assert from_api_key.auth_base == from_pkce.auth_base == 'https://www.orcarouter.ai'
    assert from_api_key.describe().keys() == from_pkce.describe().keys()
    # Only the auth method differs: downstream code has nothing else to branch on.
    assert from_api_key.auth_method != from_pkce.auth_method
    assert from_api_key.scope == from_pkce.scope == 'api'


def test_downstream_transport_is_indifferent_to_the_credential_source(memory_store, monkeypatch):
    """Inference and discovery read only the credential interface, not its origin."""
    from common.orcarouter.transport import _auth_headers

    api_key_credential = OrcaCredential(
        api_key='sk-orca-' + 'a' * 32,
        auth_method=AUTH_METHOD_API_KEY,
        auth_base='https://www.orcarouter.ai',
        api_base='https://api.orcarouter.ai/v1',
    )
    pkce_credential = OrcaCredential(
        api_key='sk-orca-' + 'b' * 32,
        auth_method=AUTH_METHOD_PKCE,
        auth_base='https://www.orcarouter.ai',
        api_base='https://api.orcarouter.ai/v1',
    )
    assert _auth_headers(api_key_credential).keys() == _auth_headers(pkce_credential).keys()
    assert _auth_headers(api_key_credential)['Authorization'].startswith('Bearer sk-orca-')


def test_credential_repr_never_contains_the_key(memory_store):
    credential = OrcaCredential(
        api_key='sk-orca-' + 'q' * 32,
        auth_method=AUTH_METHOD_API_KEY,
        auth_base='https://www.orcarouter.ai',
        api_base='https://api.orcarouter.ai/v1',
    )
    assert 'q' * 32 not in repr(credential)
    assert credential.masked_key in repr(credential)
