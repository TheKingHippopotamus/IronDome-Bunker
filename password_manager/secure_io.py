#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Permission-safe creation of everything IronDome writes to disk.

Every file under the data directory is either secret material (the vault, the
salt, the encrypted master credentials) or a record of how the vault is used
(the log, the lockout counters, the settings). None of it is another local
user's business, so all of it is created ``0600`` and every directory ``0700``.

Before 3.2.2 that guarantee rested on the ``secrets/`` directory alone: the
files inside were created by a plain ``open()``, which means ``0666`` minus the
process umask -- ``-rw-r--r--`` on a default box. The directory blocked
traversal, so nothing leaked in practice, but a single ``chmod`` on the parent,
a permissive umask, a backup tool or a copy out of ``secrets/`` removed the only
layer there was. This module makes the file mode a property of the write itself.

Two rules, in one place:

* :func:`secure_open` creates with ``O_CREAT|O_WRONLY|O_TRUNC`` at ``0600``
  *and* ``fchmod``s the descriptor. ``O_CREAT`` does not change the mode of a
  file that already exists, so the ``fchmod`` is what tightens a vault written
  by an older version -- and doing it on the descriptor means there is no
  window in which new contents sit under the old mode.
* :func:`secure_makedirs` does the same for directories at ``0700``, on
  creation and on every subsequent open of an existing vault.

``os.fchmod`` is POSIX-only; on Windows the mode bits are close to meaningless
anyway, so every call is best-effort and a failure to tighten never fails a
write.
"""

import os
from contextlib import contextmanager

__all__ = [
    "SECRET_FILE_MODE",
    "SECRET_DIR_MODE",
    "secure_open",
    "secure_write",
    "secure_makedirs",
    "ensure_secure_file",
    "harden_file",
    "harden_dir",
]

#: Owner read/write, nothing for group or other.
SECRET_FILE_MODE = 0o600

#: Owner read/write/traverse, nothing for group or other.
SECRET_DIR_MODE = 0o700


def harden_file(path):
    """chmod *path* to 0600. Returns True on success, False if it could not."""
    try:
        os.chmod(path, SECRET_FILE_MODE)
        return True
    except OSError:
        return False


def harden_dir(path):
    """chmod *path* to 0700. Returns True on success, False if it could not."""
    try:
        os.chmod(path, SECRET_DIR_MODE)
        return True
    except OSError:
        return False


def _fchmod(fd):
    """Best-effort fchmod to 0600; absent on platforms without it."""
    try:
        os.fchmod(fd, SECRET_FILE_MODE)
    except (AttributeError, NotImplementedError, OSError):
        pass


@contextmanager
def secure_open(path, mode="wb"):
    """Open *path* for writing with the file guaranteed to end up 0600.

    Args:
        path: File to create or overwrite.
        mode: ``"wb"`` (default) or ``"w"``. Only write modes are supported --
            this call always truncates, because every caller replaces the whole
            file.

    Yields:
        An open file object. Truncation and the mode change both happen before
        any caller data is written.
    """
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, SECRET_FILE_MODE)
    _fchmod(fd)
    try:
        with os.fdopen(fd, "wb" if "b" in mode else "w") as handle:
            yield handle
    finally:
        # Fallback for platforms without fchmod; a no-op when it already worked.
        harden_file(path)


def secure_write(path, data):
    """Write *data* (bytes or str) to *path* as a 0600 file."""
    binary = isinstance(data, (bytes, bytearray))
    with secure_open(path, "wb" if binary else "w") as handle:
        handle.write(data)


def secure_makedirs(path, exist_ok=True):
    """Create *path* (and parents) as 0700, and tighten it if it already exists."""
    os.makedirs(path, mode=SECRET_DIR_MODE, exist_ok=exist_ok)
    harden_dir(path)


def ensure_secure_file(path):
    """Make sure *path* exists and is 0600, without truncating it.

    Used for append-style files -- the log -- that another component opens for
    itself. Returns True if the file is present and owner-only afterwards.
    """
    try:
        fd = os.open(path, os.O_RDONLY | os.O_CREAT, SECRET_FILE_MODE)
    except OSError:
        return False
    try:
        _fchmod(fd)
    finally:
        os.close(fd)
    return harden_file(path)
