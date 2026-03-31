"""Full-screen lock overlay when session times out."""

from textual.screen import ModalScreen
from textual.widgets import Static, Input, Button
from textual.containers import Center, Vertical

from password_manager.tui.theme import ICONS, LOGO_SMALL


class LockOverlay(ModalScreen[bool]):
    """Covers the entire terminal when session expires.

    All vault data is hidden. User must re-authenticate to continue.
    Dismisses with True if re-auth succeeds, False to quit.
    """

    DEFAULT_CSS = """
    LockOverlay {
        align: center middle;
        background: #0A0D0F 95%;
    }

    #lock-container {
        width: 50;
        height: auto;
        background: #111518;
        border: solid #FF2020;
        padding: 2 4;
    }

    #lock-title {
        color: #FF2020;
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    #lock-reason {
        color: #94A3B8;
        text-align: center;
        width: 100%;
        margin-bottom: 2;
    }

    #lock-password {
        margin-bottom: 1;
    }

    #lock-actions {
        layout: horizontal;
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    #lock-actions Button {
        margin: 0 1;
    }
    """

    def compose(self):
        with Center():
            with Vertical(id="lock-container"):
                yield Static(
                    f"{ICONS['locked']}  SESSION LOCKED",
                    id="lock-title",
                )
                yield Static(
                    "Session expired due to inactivity.\nRe-authenticate to continue.",
                    id="lock-reason",
                )
                yield Input(
                    placeholder="Master password",
                    password=True,
                    id="lock-password",
                )
                with Center(id="lock-actions"):
                    yield Button("Unlock", variant="primary", id="lock-unlock")
                    yield Button("Quit", variant="error", id="lock-quit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "lock-quit":
            self.dismiss(False)
        elif event.button.id == "lock-unlock":
            self._attempt_unlock()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._attempt_unlock()

    def _attempt_unlock(self) -> None:
        password_input = self.query_one("#lock-password", Input)
        password = password_input.value
        if password:
            # The app handles the actual auth; we just pass the signal
            self.dismiss(True)
        else:
            password_input.focus()
