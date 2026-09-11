"""Origin resolution and network policy for OrcaRouter.

Authentication and inference live on **different public origins**:

* authentication and code exchange — ``https://www.orcarouter.ai``
* inference and model discovery — ``https://api.orcarouter.ai/v1``

One origin is never derived from the other by replacing a hostname or by appending
``/v1``: those two strings are unrelated, and ``api.orcarouter.ai/v1/auth/keys`` is a
404. Self-hosted deployments may run both on one origin, so ``ORCA_BASE_URL`` is a
shared fallback that both explicit overrides take precedence over.

Remote origins must be HTTPS. Plain HTTP is allowed only for loopback, which keeps
local development against a self-hosted gateway possible without weakening the
default.
"""

import ipaddress
import os
from urllib.parse import urlsplit

#: Path of the consent screen. Not an API — it is opened in a browser.
AUTHORIZE_PATH = '/auth'

#: Path that exchanges an auth code for an API key. Fixed, and *not* under ``/v1``.
EXCHANGE_PATH = '/api/v1/auth/keys'

#: Device-grant endpoints (RFC 8628). Present for documentation and tests; the
#: device grant is intentionally not one of the flows this integration ships.
DEVICE_CODE_PATH = '/api/v1/auth/device/code'
DEVICE_TOKEN_PATH = '/api/v1/auth/device/token'

AUTH_ORIGIN_DEFAULT = 'https://www.orcarouter.ai'
API_ORIGIN_DEFAULT = 'https://api.orcarouter.ai'
API_PATH_PREFIX = '/v1'

ENV_SHARED = 'ORCA_BASE_URL'
ENV_AUTH = 'ORCA_AUTH_BASE_URL'
ENV_API = 'ORCA_API_BASE_URL'

_LOOPBACK_HOSTS = frozenset({'localhost', '127.0.0.1', '[::1]', '::1'})


def _is_loopback(host: str) -> bool:
    host = (host or '').strip().lower()
    if host in _LOOPBACK_HOSTS:
        return True
    try:
        return ipaddress.ip_address(host.strip('[]')).is_loopback
    except ValueError:
        return False


def _normalize(origin: str, *, var_name: str) -> str:
    """Validate one configured origin and return it without a trailing slash."""
    origin = (origin or '').strip().rstrip('/')
    if not origin:
        raise ValueError(f'{var_name} is empty')
    parts = urlsplit(origin)
    if parts.scheme not in ('http', 'https'):
        raise ValueError(f'{var_name} must be an absolute http(s) URL, got {origin!r}')
    if not parts.hostname:
        raise ValueError(f'{var_name} has no host: {origin!r}')
    if parts.scheme != 'https' and not _is_loopback(parts.hostname):
        raise ValueError(f'{var_name} must use HTTPS unless it points at loopback, got {origin!r}')
    if parts.query or parts.fragment:
        raise ValueError(f'{var_name} must not carry a query or fragment: {origin!r}')
    return origin


def resolve_auth_base(env: dict | None = None) -> str:
    """Return the authentication origin. Explicit override > shared base > public default."""
    env = os.environ if env is None else env
    for var_name in (ENV_AUTH, ENV_SHARED):
        if env.get(var_name):
            return _normalize(env[var_name], var_name=var_name)
    return _normalize(AUTH_ORIGIN_DEFAULT, var_name='default')


def resolve_api_base(env: dict | None = None) -> str:
    """Return the inference origin *including* the ``/v1`` path prefix."""
    env = os.environ if env is None else env
    for var_name in (ENV_API, ENV_SHARED):
        if env.get(var_name):
            return _join_api_path(_normalize(env[var_name], var_name=var_name))
    return _join_api_path(_normalize(API_ORIGIN_DEFAULT, var_name='default'))


def _join_api_path(origin: str) -> str:
    if origin.endswith(API_PATH_PREFIX):
        return origin
    return f'{origin}{API_PATH_PREFIX}'


def authorize_url(auth_base: str) -> str:
    """The consent screen URL. Never built from the inference origin."""
    return f'{auth_base}{AUTHORIZE_PATH}'


def exchange_url(auth_base: str) -> str:
    """The code-exchange URL. Fixed at ``/api/v1/auth/keys`` — not ``/v1/auth/keys``."""
    return f'{auth_base}{EXCHANGE_PATH}'


def device_code_url(auth_base: str) -> str:
    return f'{auth_base}{DEVICE_CODE_PATH}'


def device_token_url(auth_base: str) -> str:
    return f'{auth_base}{DEVICE_TOKEN_PATH}'


def models_url(api_base: str, capability: str | None = None) -> str:
    """Model-catalog URL under the inference origin, optionally filtered by capability."""
    url = f'{api_base}/models'
    return f'{url}?capability={capability}' if capability else url


def chat_completions_url(api_base: str) -> str:
    return f'{api_base}/chat/completions'


def validate_callback_url(callback_url: str) -> str:
    """Validate a Flow A ``callback_url`` against the documented rules.

    ``https://`` any host and any port; ``http://`` only for loopback. No userinfo,
    no fragment.
    """
    parts = urlsplit(callback_url)
    if parts.scheme not in ('http', 'https'):
        raise ValueError('callback_url must be an absolute http(s) URL')
    if not parts.hostname:
        raise ValueError('callback_url has no host')
    if parts.username or parts.password:
        raise ValueError('callback_url must not carry userinfo')
    if parts.fragment:
        raise ValueError('callback_url must not carry a fragment')
    if parts.scheme != 'https' and not _is_loopback(parts.hostname):
        raise ValueError('http callback_url is only allowed for localhost, 127.0.0.1 or [::1]')
    return callback_url
