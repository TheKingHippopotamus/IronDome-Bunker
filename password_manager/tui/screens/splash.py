"""Splash screen — IronDome unified art, then proceeds to login."""

from typing import Optional

from textual.message import Message
from textual.screen import Screen
from textual.widgets import Static, ProgressBar
from textual.containers import Center, Vertical
from textual.timer import Timer

from password_manager import __version__
from password_manager.tui.ascii_art import SPLASH_ART


class SplashScreen(Screen):
    """Boot screen showing unified IronDome art."""

    DEFAULT_CSS = ""

    _progress: int = 0
    _timer: Optional[Timer] = None

    _status_messages = [
        "Initializing IronDome...",
        "Loading encryption engine...",
        "Verifying keychain access...",
        "Dome systems online.",
    ]

    def compose(self):
        with Center():
            with Vertical(id="splash-wrapper"):
                yield Static(SPLASH_ART, id="splash-art", markup=False)
                yield Static(
                    f"SECURE VAULT  v{__version__}",
                    id="splash-version",
                )
                yield Center(ProgressBar(total=100, show_eta=False, id="splash-bar"))
                yield Static(self._status_messages[0], id="splash-status")

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.06, self._tick)

    def _tick(self) -> None:
        try:
            self._progress += 1
            bar = self.query_one("#splash-bar", ProgressBar)
            bar.update(progress=self._progress)

            idx = min(self._progress // 25, len(self._status_messages) - 1)
            self.query_one("#splash-status", Static).update(self._status_messages[idx])

            if self._progress >= 100:
                if self._timer:
                    self._timer.stop()
                self.app.post_message(SplashScreen.Complete())
        except Exception:
            if self._timer:
                self._timer.stop()
            self.app.post_message(SplashScreen.Complete())

    def on_key(self, event) -> None:
        """Skip splash on any keypress."""
        if self._timer:
            self._timer.stop()
        self.app.post_message(SplashScreen.Complete())

    class Complete(Message):
        """Posted when the splash animation finishes."""
