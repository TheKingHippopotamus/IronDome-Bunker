"""Memory protection utilities for sensitive data."""

import ctypes
import ctypes.util
import sys


def zero_bytearray(buf: bytearray) -> None:
    """Overwrite a bytearray's buffer with zeros, then clear it.

    This is a best-effort defense-in-depth measure. Python's garbage
    collector and memory allocator may retain copies; this reduces the
    window of exposure.
    """
    if len(buf) > 0:
        ctypes.memset(
            (ctypes.c_char * len(buf)).from_buffer(buf), 0, len(buf)
        )
    buf.clear()


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
