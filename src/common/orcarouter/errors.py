"""Terminal, user-actionable OrcaRouter errors.

Every error carries a short machine-readable ``code`` and a message that is safe to
show the user. No error ever carries an API key, an auth code, or a PKCE verifier —
:meth:`OrcaRouterError.__str__` is the only representation that reaches logs and UI.
"""


class OrcaRouterError(Exception):
    """Base class for every OrcaRouter failure surfaced to the user."""

    def __init__(self, code: str, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable

    def __str__(self) -> str:
        return f'[{self.code}] {self.message}'


class CredentialError(OrcaRouterError):
    """Something is wrong with the stored or supplied credential."""


class NeedsReauthError(CredentialError):
    """The relay rejected this credential; the exact account must re-authorize.

    This is a terminal state, never a retry loop: OrcaRouter issues durable API
    keys, not refreshable OAuth tokens, so there is no refresh grant to attempt.
    """

    def __init__(self, message: str, *, auth_method: str = '', generation: int = 0):
        super().__init__('needs_reauth', message)
        self.auth_method = auth_method
        self.generation = generation


class OrcaRouterTimeout(OrcaRouterError):
    """The authorization window closed, or the user cancelled it."""

    def __init__(self, message: str = 'The OrcaRouter authorization was cancelled or timed out'):
        super().__init__('authorization_timeout', message)


class CatalogError(OrcaRouterError):
    """Live model discovery failed; callers fall back to the last known-good catalog."""

    def __init__(self, message: str):
        super().__init__('catalog_unavailable', message, retryable=True)
