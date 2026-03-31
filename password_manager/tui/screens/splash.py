"""Splash screen — boot animation with IronDome logo."""

from typing import Optional

from textual.message import Message
from textual.screen import Screen
from textual.widgets import Static, ProgressBar
from textual.containers import Center, Vertical
from textual.timer import Timer

from password_manager.tui.widgets.logo import Logo


class SplashScreen(Screen):
    """Boot screen shown for ~2.5 seconds while vault integrity is checked."""

    DEFAULT_CSS = """
    SplashScreen {
        align: center middle;
    }

    #splash-wrapper {
        width: 80;
        height: auto;
        align: center middle;
    }

    #splash-version {
        color: #4A5568;
        text-align: center;
        width: 100%;
        margin-top: 1;
    }

    #splash-bar {
        width: 50;
        margin: 2 0;
    }

    #splash-status {
        color: #94A3B8;
        text-align: center;
        width: 100%;
    }
    """

    _progress: int = 0
    _timer: Optional[Timer] = None
    _status_messages = [
        "Initializing IronDome...",
        "Checking vault integrity...",
        "Loading encryption engine...",
        "Verifying keychain access...",
        "Dome systems online.",
    ]

    def compose(self):
        with Center():
            with Vertical(id="splash-wrapper"):
                yield Logo()
                yield Static("SECURE VAULT  v2.1.1", id="splash-version")
                yield Center(ProgressBar(total=100, show_eta=False, id="splash-bar"))
                yield Static(self._status_messages[0], id="splash-status")

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.05, self._tick)

    def _tick(self) -> None:
        self._progress += 2
        bar = self.query_one("#splash-bar", ProgressBar)
        bar.update(progress=self._progress)

        # Update status message at progress milestones
        idx = min(self._progress // 20, len(self._status_messages) - 1)
        self.query_one("#splash-status", Static).update(self._status_messages[idx])

        if self._progress >= 100:
            if self._timer:
                self._timer.stop()
            self.app.post_message(SplashScreen.Complete())

    class Complete(Message):
        """Posted when the splash animation finishes."""
