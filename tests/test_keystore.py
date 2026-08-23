"""SecureKeyStore create/unlock against an in-memory keyring and a temp HOME.

The keychain is what stands behind the 'Biometric Only' mode, so its create,
retrieve, presence, delete and clear_all paths need to hold.  The biometric
prompt itself is deliberately not exercised: it is an OS authentication gate
in front of these calls, not part of them -- which is precisely the honest
limitation the README now documents.
"""

import pytest

from password_manager.keystore import (
    _KEY_AUTH_MODE,
    _KEY_MASTER_KEY,
    _KEY_RECOVERY_HASH,
    _SERVICE_NAME,
    SecureKeyStore,
)


@pytest.fixture
def store(memory_keyring):
    return SecureKeyStore(salt=b"\x11" * 16)


def test_keyring_reports_available(store):
    assert store.is_available() is True


def test_store_and_retrieve_master_key(store):
    key = store.generate_fernet_key()
    assert store.store_master_key(key) is True
    assert store.retrieve_master_key() == key


def test_has_master_key_reflects_state(store):
    assert store.has_master_key() is False
    store.store_master_key(store.generate_fernet_key())
    assert store.has_master_key() is True


def test_delete_master_key(store):
    store.store_master_key(store.generate_fernet_key())
    assert store.delete_master_key() is True
    assert store.has_master_key() is False
    assert store.retrieve_master_key() is None


def test_master_key_is_stored_encoded_not_raw(store, memory_keyring):
    key = store.generate_fernet_key()
    store.store_master_key(key)
    stored = memory_keyring.get_password(_SERVICE_NAME, _KEY_MASTER_KEY)
    assert isinstance(stored, str)
    assert stored != key.decode("ascii")


def test_auth_mode_round_trip(store):
    assert store.store_auth_mode("biometric_only") is True
    assert store.get_auth_mode() == "biometric_only"


def test_auth_mode_rejects_unknown_value(store):
    assert store.store_auth_mode("telepathy") is False
    assert store.get_auth_mode() is None


def test_recovery_key_format_is_24_hex_in_six_groups(store):
    key = store.generate_recovery_key()
    groups = key.split("-")
    assert len(groups) == 6
    assert all(len(g) == 4 for g in groups)
    assert all(c in "0123456789ABCDEF" for c in key.replace("-", ""))


def test_recovery_key_plaintext_is_never_persisted(store, memory_keyring):
    key = store.generate_recovery_key()
    assert store.store_recovery_hash(key) is True
    stored = memory_keyring.get_password(_SERVICE_NAME, _KEY_RECOVERY_HASH)
    assert stored is not None
    assert key not in stored
    assert key.replace("-", "") not in stored


def test_recovery_key_verifies_and_rejects(store):
    key = store.generate_recovery_key()
    store.store_recovery_hash(key)
    assert store.verify_recovery_key(key) is True
    assert store.verify_recovery_key(store.generate_recovery_key()) is False


def test_clear_all_removes_every_entry(store, memory_keyring):
    store.store_master_key(store.generate_fernet_key())
    store.store_auth_mode("password_only")
    store.store_recovery_hash(store.generate_recovery_key())

    assert store.clear_all() is True

    for name in (_KEY_MASTER_KEY, _KEY_AUTH_MODE, _KEY_RECOVERY_HASH):
        assert memory_keyring.get_password(_SERVICE_NAME, name) is None


def test_clear_all_is_idempotent_on_an_empty_keychain(store):
    assert store.clear_all() is True
    assert store.clear_all() is True


def test_generated_fernet_keys_are_unique(store):
    keys = {store.generate_fernet_key() for _ in range(16)}
    assert len(keys) == 16
