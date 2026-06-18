#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
IronDome self-destruct: permanently erases all user data for this installation.

``execute_nuke()`` is the single public entry point.  It performs no prompting
or confirmation — that responsibility belongs entirely to the caller (CLI or TUI).

Destruction sequence
--------------------
1. Load salt (still on disk) and clear OS keychain entries.
2. Secure-overwrite every file with random bytes, then unlink.
3. Remove directory tree under data_dir.
4. Remove data_dir itself if empty.
"""

import logging
import os
from typing import Optional

log = logging.getLogger("IronDome.Nuke")

# Top-level files that live directly under data_dir
_TOP_LEVEL_FILES = (
    "settings.json",
    "password_manager.log",
)

# Subdirectories to wipe completely
_SUBDIRS_TO_WIPE = (
    "secrets",
    "backups",
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _secure_delete_file(path: str, errors: list) -> bool:
    """Overwrite file contents with random bytes, then unlink."""
    try:
        size = os.path.getsize(path)
        if size > 0:
            with open(path, "r+b") as fh:
                fh.write(os.urandom(size))
                fh.flush()
                os.fsync(fh.fileno())
        os.unlink(path)
        return True
    except Exception as exc:
        errors.append(f"Could not delete {path}: {exc}")
        log.error("Failed to delete %s: %s", path, exc)
        return False


def _wipe_directory(dirpath: str, deleted: list, errors: list) -> None:
    """Recursively secure-delete every file in dirpath, then remove dirs."""
    if not os.path.isdir(dirpath):
        return
    for root, dirs, files in os.walk(dirpath, topdown=False):
        for filename in files:
            filepath = os.path.join(root, filename)
            if _secure_delete_file(filepath, errors):
                deleted.append(filepath)
        for dirname in dirs:
            subdirpath = os.path.join(root, dirname)
            try:
                os.rmdir(subdirpath)
            except Exception as exc:
                errors.append(f"Could not remove directory {subdirpath}: {exc}")
    try:
        os.rmdir(dirpath)
    except Exception as exc:
        errors.append(f"Could not remove directory {dirpath}: {exc}")


def _clear_keyring(data_dir: str, errors: list) -> bool:
    """Remove all IronDome entries from the OS keychain.

    Loads the salt first (while the secrets directory still exists) so that
    SecureKeyStore is fully initialised.  If storage is already gone, an
    unsalted instance is used — clear_all() does not require a salt.
    """
    try:
        from password_manager.keystore import SecureKeyStore

        salt: Optional[bytes] = None
        try:
            from password_manager.storage import PasswordStorage
            storage = PasswordStorage(data_dir)
            salt = storage.load_salt()
        except Exception:
            pass

        ks = SecureKeyStore(salt=salt, logger=log)
        return ks.clear_all()
    except Exception as exc:
        errors.append(f"Keyring clear failed: {exc}")
        log.error("Keyring clear failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_targets(data_dir: str) -> list:
    """
    Return a list of paths that execute_nuke() will destroy.

    Used by CLI/TUI to show the user exactly what will be deleted before
    asking for confirmation.

    Parameters
    ----------
    data_dir:
        Path to the IronDome data directory (typically ``~/.password_manager``).

    Returns
    -------
    list of str
        Absolute paths that exist and will be deleted.
    """
    targets = []

    for subdir in _SUBDIRS_TO_WIPE:
        dirpath = os.path.join(data_dir, subdir)
        if os.path.isdir(dirpath):
            for root, dirs, files in os.walk(dirpath):
                for filename in files:
                    targets.append(os.path.join(root, filename))
            targets.append(dirpath)

    for filename in _TOP_LEVEL_FILES:
        filepath = os.path.join(data_dir, filename)
        if os.path.isfile(filepath):
            targets.append(filepath)

    if os.path.isdir(data_dir):
        targets.append(data_dir)

    return targets


def execute_nuke(data_dir: str) -> dict:
    """
    Permanently destroy all IronDome user data for this installation.

    The caller MUST obtain explicit user confirmation before invoking this.
    This function performs no prompting of its own.

    Destruction sequence
    --------------------
    1. Clear OS keychain entries (master_key, auth_mode, recovery_hash).
    2. Secure-overwrite + unlink every file inside the secrets and backups dirs.
    3. Secure-delete top-level files (settings.json, password_manager.log).
    4. Remove directory tree; remove data_dir if now empty.

    Parameters
    ----------
    data_dir:
        Path to the IronDome data directory (typically ``~/.password_manager``).

    Returns
    -------
    dict
        ``success``         (bool) — True only if every step succeeded.
        ``files_deleted``   (list) — Absolute paths of files that were deleted.
        ``keyring_cleared`` (bool) — True if OS keychain entries were removed.
        ``errors``          (list) — Human-readable strings for any failures.
    """
    deleted: list = []
    errors: list = []

    log.warning("IronDome nuke initiated on data_dir=%s", data_dir)

    # Step 1: clear keyring before touching the disk (salt is still present)
    keyring_ok = _clear_keyring(data_dir, errors)

    # Step 2: wipe subdirectories
    for subdir in _SUBDIRS_TO_WIPE:
        _wipe_directory(os.path.join(data_dir, subdir), deleted, errors)

    # Step 3: wipe top-level files
    for filename in _TOP_LEVEL_FILES:
        filepath = os.path.join(data_dir, filename)
        if os.path.isfile(filepath):
            if _secure_delete_file(filepath, errors):
                deleted.append(filepath)

    # Step 4: remove data_dir if now empty
    try:
        if os.path.isdir(data_dir) and not os.listdir(data_dir):
            os.rmdir(data_dir)
    except Exception as exc:
        errors.append(f"Could not remove data directory {data_dir}: {exc}")

    success = not errors

    if success:
        log.warning("IronDome nuke complete. All user data destroyed.")
    else:
        log.error("IronDome nuke completed with %d error(s): %s", len(errors), errors)

    return {
        "success": success,
        "files_deleted": deleted,
        "keyring_cleared": keyring_ok,
        "errors": errors,
    }
