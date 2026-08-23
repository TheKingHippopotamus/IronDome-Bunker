"""nuke completeness.

The contract is 'overwrite and delete all vault data'.  These tests build a
data directory containing every file the package is known to write -- taken
from PasswordStorage's own path attributes plus the airspace session, the
settings file, a backup and the .device_id fallback -- and require that the
directory is gone afterwards.  They also require the inverse: if anything
survives, execute_nuke must report success=False and name the leftovers.
"""

import os

import pytest

from password_manager import nuke
from password_manager.storage import PasswordStorage


def _populate(data_dir):
    """Write every file the package creates under *data_dir*. Returns the paths."""
    storage = PasswordStorage(data_dir)
    written = []

    secret_files = [
        storage.passwords_file,
        storage.salt_file,
        storage.username_file,
        storage.password_hash_file,
        storage.login_attempts_file,
        os.path.join(data_dir, "secrets", ".airspace.session"),
    ]
    top_level = [
        storage.log_file,
        os.path.join(data_dir, "settings.json"),
        os.path.join(data_dir, ".device_id"),
    ]
    backups_dir = os.path.join(data_dir, "backups")
    os.makedirs(backups_dir, exist_ok=True)
    backups = [os.path.join(backups_dir, ".passwords_backup_20260101.enc")]

    for path in secret_files + top_level + backups:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(b"sensitive-bytes-" + os.path.basename(path).encode())
        written.append(path)
    return written


@pytest.fixture
def populated_dir(data_dir, memory_keyring):
    _populate(data_dir)
    return data_dir


def test_populate_helper_covers_device_id(populated_dir):
    assert os.path.isfile(os.path.join(populated_dir, ".device_id"))


def test_list_targets_includes_device_id(populated_dir):
    targets = nuke.list_targets(populated_dir)
    assert any(t.endswith("/.device_id") or t.endswith("\\.device_id") for t in targets)


def test_list_targets_covers_every_file_present(populated_dir):
    on_disk = set()
    for root, _dirs, files in os.walk(populated_dir):
        for name in files:
            on_disk.add(os.path.join(root, name))
    targets = set(nuke.list_targets(populated_dir))
    assert on_disk <= targets, f"not targeted: {sorted(on_disk - targets)}"


def test_nuke_leaves_nothing_behind(populated_dir):
    result = nuke.execute_nuke(populated_dir)
    assert result["errors"] == []
    assert result["success"] is True
    assert not os.path.exists(populated_dir), "data directory survived the nuke"


def test_nuke_reports_the_files_it_deleted(populated_dir):
    expected = set()
    for root, _dirs, files in os.walk(populated_dir):
        for name in files:
            expected.add(os.path.join(root, name))
    result = nuke.execute_nuke(populated_dir)
    assert set(result["files_deleted"]) == expected


def test_nuke_clears_the_keychain_first(data_dir, memory_keyring):
    from password_manager.keystore import SecureKeyStore

    _populate(data_dir)
    store = SecureKeyStore(salt=b"\x22" * 16)
    store.store_master_key(store.generate_fernet_key())
    store.store_auth_mode("password_only")

    result = nuke.execute_nuke(data_dir)

    assert result["keyring_cleared"] is True
    assert store.retrieve_master_key() is None
    assert store.get_auth_mode() is None


def test_nuke_fails_when_something_survives(data_dir, memory_keyring):
    """A stray file the target list does not know about must not be papered over."""
    _populate(data_dir)
    stray = os.path.join(data_dir, "not-a-known-target.dat")
    with open(stray, "wb") as fh:
        fh.write(b"survivor")

    result = nuke.execute_nuke(data_dir)

    assert result["success"] is False
    assert os.path.isdir(data_dir)
    assert any("not-a-known-target.dat" in e for e in result["errors"]), result["errors"]


def test_nuke_names_every_leftover(data_dir, memory_keyring):
    _populate(data_dir)
    for name in ("leftover-a", "leftover-b"):
        with open(os.path.join(data_dir, name), "wb") as fh:
            fh.write(b"x")

    result = nuke.execute_nuke(data_dir)

    joined = " ".join(result["errors"])
    assert result["success"] is False
    assert "leftover-a" in joined and "leftover-b" in joined


def test_nuke_overwrites_before_unlinking(data_dir, memory_keyring, monkeypatch):
    """The bytes must be overwritten in place, not merely unlinked."""
    _populate(data_dir)
    overwritten = []
    real_urandom = os.urandom

    def spy(n):
        overwritten.append(n)
        return real_urandom(n)

    monkeypatch.setattr(nuke.os, "urandom", spy)
    nuke.execute_nuke(data_dir)
    assert overwritten, "no file was overwritten with random bytes"


def test_nuke_on_an_absent_directory_is_not_a_success_lie(tmp_path, memory_keyring):
    missing = str(tmp_path / "never-created")
    result = nuke.execute_nuke(missing)
    assert result["success"] is True
    assert result["files_deleted"] == []
    assert not os.path.exists(missing)


def test_top_level_file_list_is_a_superset_of_known_writes():
    assert ".device_id" in nuke._TOP_LEVEL_FILES
    assert "settings.json" in nuke._TOP_LEVEL_FILES
    assert "password_manager.log" in nuke._TOP_LEVEL_FILES
