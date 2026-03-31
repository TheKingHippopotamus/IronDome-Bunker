"""Terminal cleanup and signal handling for safe exit.

Guarantees the terminal is restored even on SIGTERM, SIGINT, SIGHUP.
Clears clipboard on exit regardless of how the app terminates.
"""

import atexit
import signal
import sys

from password_manager.tui.security.clipboard import force_clear as _clipboard_clear


def _emergency_cleanup(signum=None, frame=None) -> None:
    """Restore terminal state and clear clipboard on any termination signal."""
    try:
        # Exit alternate screen buffer
        sys.stdout.write("\x1b[?1049l")
        # Show cursor
        sys.stdout.write("\x1b[?25h")
        # Clear current line
        sys.stdout.write("\x1b[2K\r")
        sys.stdout.flush()
    except (OSError, ValueError):
        pass

    try:
        _clipboard_clear()
    except Exception:
        pass

    if signum is not None:
        sys.exit(0)


def install_signal_handlers() -> None:
    """Register cleanup handlers for all termination signals.

    Call this once before launching the Textual app.
    """
    # atexit — runs on normal exit and uncaught exceptions
    atexit.register(_emergency_cleanup)

    # SIGINT (Ctrl+C), SIGTERM (kill), SIGHUP (terminal closed)
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _emergency_cleanup)

    # SIGHUP is not available on Windows
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, _emergency_cleanup)
