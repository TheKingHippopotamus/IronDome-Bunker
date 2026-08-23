"""Shared fixtures.

Every test runs against a throwaway HOME and an in-memory keyring.  Nothing
here touches a real vault, a real OS keychain, a TTY or a biometric sensor:
the suite must be runnable on a headless CI box with no user session.
"""

import os
import sys

import pytest

# Marks the process as a test run for any code that wants to opt out of
# interactive behaviour.  Set before password_manager is imported anywhere.
os.environ.setdefault("IRONDOME_TESTING", "1")


@pytest.fixture(autouse=True)
def temp_home(tmp_path, monkeypatch):
    """Point HOME (and the Windows equivalent) at a per-test directory.

    Autouse, because ``encryption.get_machine_id`` and the storage layer both
    resolve paths through ``os.path.expanduser("~")``.
    """
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("XDG_DATA_HOME", str(home / ".local" / "share"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    # expanduser consults pwd on POSIX when HOME is unset; it is set, so this
    # assertion documents that the redirect actually took effect.
    assert os.path.expanduser("~") == str(home)
    return home


class InMemoryKeyring:
    """Minimal keyring backend that stores secrets in a dict.

    The real backend on Linux is the Secret Service over D-Bus, which needs a
    logged-in session.  Substituting a dict keeps the SecureKeyStore logic
    under test -- encoding, presence checks, deletion -- without needing one.
    """

    priority = 1

    def __init__(self):
        self._store = {}

    def get_password(self, service, username):
        return self._store.get((service, username))

    def set_password(self, service, username, password):
        self._store[(service, username)] = password

    def delete_password(self, service, username):
        try:
            del self._store[(service, username)]
        except KeyError:
            import keyring.errors

            raise keyring.errors.PasswordDeleteError(username)


@pytest.fixture
def memory_keyring(monkeypatch):
    """Install the in-memory backend into the already-imported keystore module."""
    keyring = pytest.importorskip("keyring")
    from password_manager import keystore

    backend = InMemoryKeyring()
    monkeypatch.setattr(keystore, "_keyring_lib", backend)
    monkeypatch.setattr(keystore, "_KEYRING_IMPORT_OK", True)
    monkeypatch.setattr(keyring, "get_keyring", lambda: backend, raising=False)
    return backend


@pytest.fixture
def data_dir(tmp_path):
    """An empty IronDome data directory, isolated from HOME."""
    d = tmp_path / "data"
    d.mkdir()
    return str(d)


def pytest_report_header(config):
    return f"IronDome test suite — python {sys.version.split()[0]}, HOME redirected per test"
