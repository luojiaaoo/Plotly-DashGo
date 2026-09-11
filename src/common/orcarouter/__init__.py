"""OrcaRouter integration for DashGo.

Two explicit ways to obtain the same kind of credential (an ``sk-orca-…`` API key):

* :data:`AUTH_METHOD_API_KEY` — the user pastes a key they already hold;
* :data:`AUTH_METHOD_PKCE` — the user authorizes in a browser via OAuth 2.0 + PKCE.

Both adapters write through the same :class:`~common.orcarouter.credentials.CredentialStore`
seam, and everything downstream (inference transport, model discovery, capability
filtering) is unaware of which adapter produced the key.
"""

AUTH_METHOD_API_KEY = 'orcarouter'
AUTH_METHOD_PKCE = 'orcarouter-oauth'

AUTH_METHOD_LABELS = {
    AUTH_METHOD_API_KEY: 'OrcaRouter - API',
    AUTH_METHOD_PKCE: 'OrcaRouter - Auth',
}

AUTH_METHODS = (AUTH_METHOD_API_KEY, AUTH_METHOD_PKCE)

#: Where a user manages and revokes the keys this app holds.
CONSOLE_AUTHORIZED_APPS_URL = 'https://www.orcarouter.ai/console/authorized-apps'
