"""File permissions on everything the package writes.

The claim being tested is narrow and checkable: after a vault has been built
and used, *every* file under the data directory is ``0600`` and *every*
directory is ``0700``. Not "the secrets directory is 0700 and the files inside
inherit protection from it" -- that was the state before 3.2.2, and it made the
directory the only thing standing between another local account and the
encrypted vault, the salt and the encrypted master credentials.

The walk below is deliberately blind: it asserts on whatever is on disk rather
than on a list of filenames kept in the test. A file added by a future version
and written with a plain ``open()`` fails this test without anyone having to
remember to add it here.
"""

import os
import stat

import pytest

from password_manager import encryption, secure_io
from password_manager.airspace import Airspace
from password_manager.logger import setup_logger
from password_manager.session import SessionManager
from password_manager.settings import Settings
from password_manager.storage import PasswordStorage

pytestmark = pytest.mark.skipif(
    os.name == "nt", reason="POSIX mode bits are not meaningful on Windows"
)

EXPECTED_FILE_MODE = 0o600
EXPECTED_DIR_MODE = 0o700


def _mode(path):
    return stat.S_IMODE(os.stat(path).st_mode)


def _build_used_vault(data_dir):
    """Exercise every writer in the package against *data_dir*.

    Returns the list of files that ended up on disk, so a test can assert the
    vault was actually populated rather than passing over an empty directory.
    """
    from cryptography.fernet import Fernet

    storage = PasswordStorage(data_dir)
    fernet = Fernet(Fernet.generate_key())

    storage.save_salt(os.urandom(16))
    storage.save_master_username(b"encrypted-username-blob")
    storage.save_password_hash(b"encrypted-hash-blob")
    storage.save_passwords([{"site": "example.com", "password": "hunter2"}], fernet)
    storage.create_backup()

    SessionManager(storage.login_attempts_file)._save_login_attempts({"machine": {"count": 1}})
    Settings(data_dir).set("password_length", 24)
    setup_logger(storage.log_file).info("permissions test")
    Airspace(data_dir).open(timeout=60)

    return _walk(data_dir)[0]


def _walk(root):
    """Return (files, dirs) under *root*, root included in dirs."""
    files, dirs = [], [root]
    for parent, dirnames, filenames in os.walk(root):
        dirs.extend(os.path.join(parent, d) for d in dirnames)
        files.extend(os.path.join(parent, f) for f in filenames)
    return files, dirs


# ---------------------------------------------------------------------------
# The headline assertion
# ---------------------------------------------------------------------------

def test_every_file_under_data_dir_is_0600(data_dir):
    files = _build_used_vault(data_dir)
    assert files, "the vault builder wrote nothing -- the walk would pass vacuously"

    loose = {f: oct(_mode(f)) for f in files if _mode(f) != EXPECTED_FILE_MODE}
    assert not loose, f"world- or group-readable files: {loose}"


def test_every_directory_under_data_dir_is_0700(data_dir):
    _build_used_vault(data_dir)
    _files, dirs = _walk(data_dir)

    loose = {d: oct(_mode(d)) for d in dirs if _mode(d) != EXPECTED_DIR_MODE}
    assert not loose, f"traversable directories: {loose}"


def test_the_named_secrets_files_are_all_present_and_0600(data_dir):
    """The four files the review named, checked by name as well as by walk."""
    _build_used_vault(data_dir)
    storage = PasswordStorage(data_dir)

    for path in (
        storage.salt_file,
        storage.password_hash_file,
        storage.username_file,
        storage.passwords_file,
    ):
        assert os.path.isfile(path), f"missing: {path}"
        assert _mode(path) == EXPECTED_FILE_MODE, f"{path} is {oct(_mode(path))}"


def test_backup_copies_are_0600(data_dir):
    """A backup is a full copy of the vault and gets the vault's own mode."""
    _build_used_vault(data_dir)
    backups_dir = os.path.join(data_dir, "backups")
    backups = os.listdir(backups_dir)

    assert backups, "no backup was written"
    assert _mode(backups_dir) == EXPECTED_DIR_MODE
    for name in backups:
        assert _mode(os.path.join(backups_dir, name)) == EXPECTED_FILE_MODE


def test_device_id_fallback_is_0600(tmp_path, monkeypatch):
    """The .device_id written by the machine-id fallback is a secret too."""
    real_exists = os.path.exists

    def no_machine_id(path):
        if "machine-id" in str(path):
            raise OSError("machine-id unreadable")
        return real_exists(path)

    monkeypatch.setattr(encryption.os.path, "exists", no_machine_id)

    device_id = encryption.get_machine_id()
    path = os.path.join(os.path.expanduser("~"), ".password_manager", ".device_id")

    assert os.path.isfile(path), f"fallback did not write {path} (got {device_id!r})"
    assert _mode(path) == EXPECTED_FILE_MODE
    assert _mode(os.path.dirname(path)) == EXPECTED_DIR_MODE


# ---------------------------------------------------------------------------
# Upgrade path: a vault written by an older, looser version
# ---------------------------------------------------------------------------

def test_rewriting_a_world_readable_file_tightens_it(data_dir):
    """O_CREAT leaves an existing file's mode alone; the fchmod must not."""
    storage = PasswordStorage(data_dir)
    storage.save_salt(b"x" * 16)
    os.chmod(storage.salt_file, 0o644)

    storage.save_salt(b"y" * 16)

    assert _mode(storage.salt_file) == EXPECTED_FILE_MODE


def test_reopening_a_loose_data_dir_tightens_it(data_dir):
    """A 0755 data directory from an older version is corrected on open."""
    PasswordStorage(data_dir)
    os.chmod(data_dir, 0o755)
    os.chmod(os.path.join(data_dir, "secrets"), 0o755)

    PasswordStorage(data_dir)

    assert _mode(data_dir) == EXPECTED_DIR_MODE
    assert _mode(os.path.join(data_dir, "secrets")) == EXPECTED_DIR_MODE


# ---------------------------------------------------------------------------
# The helper itself
# ---------------------------------------------------------------------------

def test_secure_open_ignores_a_permissive_umask(tmp_path):
    """0600 must come from the write, not from whatever umask is in force."""
    path = str(tmp_path / "secret.bin")
    previous = os.umask(0o000)
    try:
        with secure_io.secure_open(path) as handle:
            handle.write(b"data")
    finally:
        os.umask(previous)

    assert _mode(path) == EXPECTED_FILE_MODE


def test_secure_open_truncates(tmp_path):
    path = str(tmp_path / "secret.bin")
    secure_io.secure_write(path, b"a-long-first-write")
    secure_io.secure_write(path, b"short")

    with open(path, "rb") as handle:
        assert handle.read() == b"short"


def test_secure_makedirs_ignores_a_permissive_umask(tmp_path):
    path = str(tmp_path / "nested" / "dir")
    previous = os.umask(0o000)
    try:
        secure_io.secure_makedirs(path)
    finally:
        os.umask(previous)

    assert _mode(path) == EXPECTED_DIR_MODE


def test_ensure_secure_file_tightens_without_truncating(tmp_path):
    path = str(tmp_path / "vault.log")
    with open(path, "w") as handle:
        handle.write("existing line\n")
    os.chmod(path, 0o644)

    assert secure_io.ensure_secure_file(path) is True
    assert _mode(path) == EXPECTED_FILE_MODE
    with open(path) as handle:
        assert handle.read() == "existing line\n"
