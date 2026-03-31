"""Custom Textual messages for cross-widget communication."""

from textual.message import Message


class AuthSuccess(Message):
    """Fired when authentication succeeds."""

    def __init__(self, username: str) -> None:
        self.username = username
        super().__init__()


class AuthFailed(Message):
    """Fired when authentication fails."""

    def __init__(self, reason: str = "Authentication failed") -> None:
        self.reason = reason
        super().__init__()


class SessionExpired(Message):
    """Fired when the session timer reaches zero."""


class AirspaceChanged(Message):
    """Fired when airspace state changes (open/close)."""

    def __init__(self, is_open: bool, remaining_seconds: int = 0) -> None:
        self.is_open = is_open
        self.remaining_seconds = remaining_seconds
        super().__init__()


class VaultUpdated(Message):
    """Fired when vault contents change (save/delete/import)."""


class PasswordCopied(Message):
    """Fired when a password is copied to clipboard."""

    def __init__(self, label: str, timeout: int = 30) -> None:
        self.label = label
        self.timeout = timeout
        super().__init__()


class ClipboardCleared(Message):
    """Fired when the clipboard auto-clear timer expires."""
