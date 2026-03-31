"""Cross-platform clipboard management with auto-clear."""

import subprocess
import sys
import threading
from typing import Optional


# Active clear timer — cancelled if a new copy happens before it fires
_clear_timer: Optional[threading.Timer] = None


def _platform_copy(text: str) -> bool:
    """Copy text to system clipboard. Returns True on success."""
    try:
        if sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text.encode(), check=True, timeout=5)
        elif sys.platform == "linux":
            # Try xclip first, fall back to xsel
            for cmd in (["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]):
                try:
                    subprocess.run(cmd, input=text.encode(), check=True, timeout=5)
                    return True
                except FileNotFoundError:
                    continue
            return False
        elif sys.platform == "win32":
            subprocess.run(["clip"], input=text.encode(), check=True, timeout=5)
        else:
            return False
        return True
    except (subprocess.SubprocessError, OSError):
        return False


def _platform_clear() -> None:
    """Clear the system clipboard."""
    _platform_copy("")


def copy_with_auto_clear(secret: str, timeout: int = 30) -> bool:
    """Copy secret to clipboard and schedule auto-clear after timeout seconds.

    Args:
        secret: The text to copy.
        timeout: Seconds before auto-clear. 0 disables auto-clear.

    Returns:
        True if the copy succeeded.
    """
    global _clear_timer

    # Cancel any pending clear from a previous copy
    if _clear_timer is not None:
        _clear_timer.cancel()
        _clear_timer = None

    if not _platform_copy(secret):
        return False

    if timeout > 0:
        _clear_timer = threading.Timer(timeout, _platform_clear)
        _clear_timer.daemon = True
        _clear_timer.start()

    return True


def force_clear() -> None:
    """Immediately clear the clipboard and cancel any pending timer."""
    global _clear_timer
    if _clear_timer is not None:
        _clear_timer.cancel()
        _clear_timer = None
    _platform_clear()
