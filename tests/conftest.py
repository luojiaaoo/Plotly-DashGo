"""Shared fixtures for the OrcaRouter tests.

Tests never touch the network, never use a real ``sk-orca-`` credential, and never
touch the project database: the credential store is swapped for an in-memory one that
implements exactly the same seam.
"""

import os
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# The project loads its locale catalogs through paths relative to the process working
# directory (`./translations/...` in src/i18n.py) and is always started from `src/`
# (see src/app.py). Running the suite from the same place is what makes the Dash layer
# importable exactly as it is in production.
os.chdir(SRC)

# A syntactically valid but entirely fake key. Never a real credential.
FAKE_API_KEY = 'sk-orca-' + 'test' * 8


@pytest.fixture(autouse=True)
def clean_orca_env(monkeypatch):
    """Every test starts from the public default origins and no shared base."""
    for var in ('ORCA_BASE_URL', 'ORCA_AUTH_BASE_URL', 'ORCA_API_BASE_URL'):
        monkeypatch.delenv(var, raising=False)
    yield


@pytest.fixture
def memory_store():
    from common.orcarouter.credentials import InMemoryCredentialStore

    return InMemoryCredentialStore()


@pytest.fixture(autouse=True)
def isolated_runtime(memory_store):
    """Point the runtime facade at an in-memory store for the duration of a test."""
    from common.orcarouter import runtime

    runtime.set_store(memory_store)
    yield memory_store
    runtime.set_store(None)


@pytest.fixture
def fake_key():
    return FAKE_API_KEY


def pytest_configure(config):
    config.addinivalue_line('markers', 'slow: end-to-end flow tests that bind a loopback socket')
    config.addinivalue_line('markers', 'e2e: real-browser tests that need a running DashGo instance')
