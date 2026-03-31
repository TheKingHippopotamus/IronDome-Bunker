"""Modal overlay shown during OS biometric prompt (Touch ID / Windows Hello)."""

from textual.screen import ModalScreen
from textual.widgets import Static, LoadingIndicator
from textual.containers import Center, Vertical

from password_manager.tui.theme import ICONS


class BiometricModal(ModalScreen[bool]):
    """Displays a spinner while the OS biometric dialog is active.

    The actual biometric prompt renders outside the terminal (OS-level).
    This modal prevents user interaction with the TUI during the prompt.
    Dismisses with True/False based on auth result.
    """

    DEFAULT_CSS = ""

    def __init__(self, bio_type: str = "Biometric", **kwargs) -> None:
        super().__init__(**kwargs)
        self.bio_type = bio_type

    def compose(self):
        with Center():
            with Vertical(id="biometric-container"):
                yield Static(
                    f"{ICONS['shield']}  {self.bio_type} Verification",
                    id="biometric-title",
                )
                yield Center(LoadingIndicator())
                yield Static(
                    f"Complete {self.bio_type} prompt to continue...",
                    id="biometric-hint",
                )
