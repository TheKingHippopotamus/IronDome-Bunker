"""Memory protection utilities for sensitive data.

Only swap avoidance lives here.  A ``zero_bytearray`` helper used to sit
alongside ``lock_memory`` and had no callers anywhere in the tree, while the
README advertised "bytearray zeroing" as a shipped control.  It was removed
rather than wired up: the vault key is held as an immutable Python ``bytes``
inside a ``Fernet`` object, so zeroing it in place is not possible without
changing how the key is held.  The README no longer claims it.
"""

import ctypes
import ctypes.util
import sys


def lock_memory() -> bool:
    """Attempt to lock process memory to prevent swapping to disk.

    Uses mlockall on Linux/macOS. No-op on Windows.
    Returns True if successful or not applicable.
    """
    if sys.platform == "win32":
        return True

    libc_name = ctypes.util.find_library("c")
    if not libc_name:
        return False

    try:
        libc = ctypes.CDLL(libc_name, use_errno=True)
        MCL_CURRENT = 1
        MCL_FUTURE = 2
        result = libc.mlockall(MCL_CURRENT | MCL_FUTURE)
        return result == 0
    except (OSError, AttributeError):
        return False
