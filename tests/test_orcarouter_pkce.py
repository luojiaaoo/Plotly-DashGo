"""PKCE primitives, origin resolution and the exchange contract."""

import re
from urllib.parse import parse_qs, urlsplit

import pytest

from common.orcarouter import origins
from common.orcarouter.errors import CredentialError
from common.orcarouter.pkce import (
    FLOW_LOOPBACK,
    FLOW_OUT_OF_BAND,
    OOB_CALLBACK_URL,
    PkceAttempt,
    b64url,
    code_challenge,
    new_state,
    new_verifier,
    parse_exchange_response,
    state_matches,
)

# --------------------------------------------------------------------------------------
# Origins
# --------------------------------------------------------------------------------------


def test_default_origins_are_distinct_and_correct():
    assert origins.resolve_auth_base({}) == 'https://www.orcarouter.ai'
    assert origins.resolve_api_base({}) == 'https://api.orcarouter.ai/v1'


def test_exchange_path_is_not_under_v1():
    """The single most common integration mistake: /v1/auth/keys is a 404."""
    url = origins.exchange_url('https://www.orcarouter.ai')
    assert url == 'https://www.orcarouter.ai/api/v1/auth/keys'
    assert '/v1/auth/keys' not in url.replace('/api/v1/auth/keys', '')
    assert origins.authorize_url('https://www.orcarouter.ai') == 'https://www.orcarouter.ai/auth'


def test_auth_origin_is_never_derived_from_api_origin():
    """An api-only override must not move the auth origin, and vice versa."""
    assert origins.resolve_auth_base({'ORCA_API_BASE_URL': 'https://api.example.test'}) == 'https://www.orcarouter.ai'
    assert origins.resolve_api_base({'ORCA_AUTH_BASE_URL': 'https://auth.example.test'}) == 'https://api.orcarouter.ai/v1'


def test_shared_base_is_a_fallback_and_explicit_overrides_win():
    shared = {'ORCA_BASE_URL': 'https://orca.internal'}
    assert origins.resolve_auth_base(shared) == 'https://orca.internal'
    assert origins.resolve_api_base(shared) == 'https://orca.internal/v1'

    both = {**shared, 'ORCA_AUTH_BASE_URL': 'https://auth.internal', 'ORCA_API_BASE_URL': 'https://api.internal'}
    assert origins.resolve_auth_base(both) == 'https://auth.internal'
    assert origins.resolve_api_base(both) == 'https://api.internal/v1'


def test_api_base_does_not_double_the_v1_suffix():
    assert origins.resolve_api_base({'ORCA_API_BASE_URL': 'https://api.internal/v1'}) == 'https://api.internal/v1'


@pytest.mark.parametrize('bad', ['http://orca.example.com', 'ftp://orca.example.com', 'orca.example.com'])
def test_remote_origins_must_be_https(bad):
    with pytest.raises(ValueError):
        origins.resolve_auth_base({'ORCA_AUTH_BASE_URL': bad})


def test_empty_override_falls_back_to_the_default():
    """An unset-but-present env var is not a configuration; it must not crash."""
    assert origins.resolve_auth_base({'ORCA_AUTH_BASE_URL': ''}) == 'https://www.orcarouter.ai'


@pytest.mark.parametrize('good', ['http://127.0.0.1:8080', 'http://localhost:9000', 'http://[::1]:9000'])
def test_http_is_allowed_for_loopback(good):
    assert origins.resolve_auth_base({'ORCA_AUTH_BASE_URL': good}) == good


def test_callback_url_rules():
    assert origins.validate_callback_url('http://127.0.0.1:51733/cb')
    assert origins.validate_callback_url('https://dashgo.example.com/cb')  # any https host/port
    for bad in ('http://evil.example.com/cb', 'http://127.0.0.1/cb#frag', 'http://user:pw@127.0.0.1/cb'):
        with pytest.raises(ValueError):
            origins.validate_callback_url(bad)


def test_models_url_carries_capability():
    base = 'https://api.orcarouter.ai/v1'
    assert origins.models_url(base) == 'https://api.orcarouter.ai/v1/models'
    assert origins.models_url(base, 'chat') == 'https://api.orcarouter.ai/v1/models?capability=chat'


# --------------------------------------------------------------------------------------
# Verifier / challenge / state
# --------------------------------------------------------------------------------------


def test_challenge_is_unpadded_base64url_sha256_of_verifier():
    import hashlib

    verifier = new_verifier()
    assert '=' not in verifier
    assert re.fullmatch(r'[A-Za-z0-9_-]+', verifier)
    expected = b64url(hashlib.sha256(verifier.encode('ascii')).digest())
    assert code_challenge(verifier) == expected
    assert '=' not in code_challenge(verifier)


def test_verifier_and_state_are_fresh_from_a_crypto_rng_every_time():
    verifiers = {new_verifier() for _ in range(50)}
    states = {new_state() for _ in range(50)}
    assert len(verifiers) == 50
    assert len(states) == 50
    # 32 random bytes -> 43 base64url characters, not a timestamp or a counter.
    assert all(len(v) == 43 for v in verifiers)


def test_state_comparison_is_constant_time_and_rejects_mismatch():
    state = new_state()
    assert state_matches(state, state)
    assert not state_matches(state, new_state())
    assert not state_matches(state, '')
    assert not state_matches('', state)


def test_authorize_url_carries_challenge_and_never_the_verifier():
    attempt = PkceAttempt(flow=FLOW_OUT_OF_BAND, callback_url=OOB_CALLBACK_URL, app_name='DashGo')
    url = attempt.build_authorize_url('https://www.orcarouter.ai')
    query = parse_qs(urlsplit(url).query)

    assert urlsplit(url).path == '/auth'
    assert urlsplit(url).netloc == 'www.orcarouter.ai'
    assert query['callback_url'] == ['oob']
    assert query['code_challenge_method'] == ['S256']
    assert query['code_challenge'] == [attempt.challenge()]
    assert query['scope'] == ['api']
    assert query['state'] == [attempt.state]
    # The verifier must not be in the URL, under any parameter name.
    assert attempt.verifier not in url
    assert attempt.verifier not in query.values().__str__()


def test_loopback_authorize_url_uses_the_real_callback_address():
    attempt = PkceAttempt(flow=FLOW_LOOPBACK, callback_url='http://127.0.0.1:51733/cb')
    query = parse_qs(urlsplit(attempt.build_authorize_url('https://www.orcarouter.ai')).query)
    assert query['callback_url'] == ['http://127.0.0.1:51733/cb']
    assert query['code_challenge_method'] == ['S256']


def test_exchange_body_is_the_only_place_the_verifier_appears():
    attempt = PkceAttempt(flow=FLOW_OUT_OF_BAND, callback_url=OOB_CALLBACK_URL)
    body = attempt.exchange_body('the-code')
    assert body['code_verifier'] == attempt.verifier
    assert body['code_challenge_method'] == 'S256'
    assert body['code'] == 'the-code'
    # And the attempt's own repr must not leak it.
    assert attempt.verifier not in repr(attempt)


def test_exchange_body_rejects_a_missing_code():
    attempt = PkceAttempt(flow=FLOW_OUT_OF_BAND, callback_url=OOB_CALLBACK_URL)
    with pytest.raises(CredentialError):
        attempt.exchange_body('   ')


def test_plain_is_never_offered():
    attempt = PkceAttempt(flow=FLOW_OUT_OF_BAND, callback_url=OOB_CALLBACK_URL)
    assert attempt.challenge() != attempt.verifier


def test_unsupported_scope_is_refused_before_a_code_is_minted():
    with pytest.raises(ValueError):
        PkceAttempt(flow=FLOW_OUT_OF_BAND, callback_url=OOB_CALLBACK_URL, scope='admin')


# --------------------------------------------------------------------------------------
# Exchange response contract
# --------------------------------------------------------------------------------------


def test_successful_exchange_returns_key_and_granted_scope():
    key, scope, user_id = parse_exchange_response(200, {'key': 'sk-orca-abc', 'scope': 'api', 'user_id': '42'})
    assert (key, scope, user_id) == ('sk-orca-abc', 'api', '42')


def test_granted_scope_is_read_back_not_assumed():
    """A downgraded grant must be reported, not silently accepted."""
    with pytest.raises(CredentialError) as exc:
        parse_exchange_response(200, {'key': 'sk-orca-abc', 'scope': 'read-only'})
    assert exc.value.code == 'scope_downgrade'


def test_missing_scope_is_a_downgrade():
    with pytest.raises(CredentialError) as exc:
        parse_exchange_response(200, {'key': 'sk-orca-abc'})
    assert exc.value.code == 'scope_downgrade'


@pytest.mark.parametrize(
    'status,code',
    [(400, 'exchange_rejected'), (403, 'code_rejected'), (429, 'rate_limited'), (500, 'exchange_failed')],
)
def test_documented_failure_statuses_map_to_specific_errors(status, code):
    with pytest.raises(CredentialError) as exc:
        parse_exchange_response(status, {})
    assert exc.value.code == code


def test_exchange_errors_never_echo_the_response_body():
    """A relay that reflects the request must not leak the verifier back into the UI."""
    secret = 'sk-orca-super-secret-value'
    with pytest.raises(CredentialError) as exc:
        parse_exchange_response(403, {'error': 'bad', 'echo': secret, 'code_verifier': 'v' * 43})
    assert secret not in str(exc.value)
    assert 'v' * 43 not in str(exc.value)
