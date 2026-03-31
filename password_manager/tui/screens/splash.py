"""Splash screen — cycles through 3 ASCII art designs, then proceeds to login."""

from typing import Optional

from textual.message import Message
from textual.screen import Screen
from textual.widgets import Static, ProgressBar
from textual.containers import Center, Vertical
from textual.timer import Timer

from password_manager import __version__
from password_manager.tui.ascii_art import SPLASH_RADAR, SPLASH_PROFILE, SPLASH_BADGE


_SPLASH_ARTS = [SPLASH_RADAR, SPLASH_PROFILE, SPLASH_BADGE]
_ART_LABELS = ["RADAR VIEW", "SIDE PROFILE", "SHIELD BADGE"]
_CYCLE_SECONDS = 3
_TOTAL_CYCLES = 3  # Show all 3, then proceed


class SplashScreen(Screen):
    """Boot screen that cycles through 3 IronDome ASCII art designs."""

    DEFAULT_CSS = ""

    _current_art: int = 0
    _cycle_timer: Optional[Timer] = None
    _progress_timer: Optional[Timer] = None
    _progress: int = 0

    _status_messages = [
        "Initializing IronDome...",
        "Loading encryption engine...",
        "Dome systems online.",
    ]

    def compose(self):
        with Center():
            with Vertical(id="splash-wrapper"):
                yield Static(_SPLASH_ARTS[0], id="splash-art", markup=False)
                yield Static(
                    f"SECURE VAULT  v{__version__}  —  {_ART_LABELS[0]}",
                    id="splash-version",
                )
                yield Center(ProgressBar(total=100, show_eta=False, id="splash-bar"))
                yield Static(self._status_messages[0], id="splash-status")

    def on_mount(self) -> None:
        self._cycle_timer = self.set_interval(_CYCLE_SECONDS, self._next_art)
        self._progress_timer = self.set_interval(0.09, self._tick_progress)

    def _next_art(self) -> None:
        try:
            self._current_art += 1
            if self._current_art >= _TOTAL_CYCLES:
                # All 3 shown — done
                if self._cycle_timer:
                    self._cycle_timer.stop()
                if self._progress_timer:
                    self._progress_timer.stop()
                self.app.post_message(SplashScreen.Complete())
                return

            art_widget = self.query_one("#splash-art", Static)
            art_widget.update(_SPLASH_ARTS[self._current_art])

            version_widget = self.query_one("#splash-version", Static)
            version_widget.update(
                f"SECURE VAULT  v{__version__}  —  {_ART_LABELS[self._current_art]}"
            )

            status_widget = self.query_one("#splash-status", Static)
            idx = min(self._current_art, len(self._status_messages) - 1)
            status_widget.update(self._status_messages[idx])
        except Exception:
            if self._cycle_timer:
                self._cycle_timer.stop()
            if self._progress_timer:
                self._progress_timer.stop()
            self.app.post_message(SplashScreen.Complete())

    def _tick_progress(self) -> None:
        try:
            total_ticks = (_CYCLE_SECONDS * _TOTAL_CYCLES) / 0.09
            self._progress = min(100, self._progress + int(100 / total_ticks) + 1)
            bar = self.query_one("#splash-bar", ProgressBar)
            bar.update(progress=self._progress)
        except Exception:
            pass

    def on_key(self, event) -> None:
        """Skip splash on any keypress."""
        if self._cycle_timer:
            self._cycle_timer.stop()
        if self._progress_timer:
            self._progress_timer.stop()
        self.app.post_message(SplashScreen.Complete())

    class Complete(Message):
        """Posted when the splash animation finishes."""
