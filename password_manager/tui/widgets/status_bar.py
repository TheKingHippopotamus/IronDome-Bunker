"""Persistent status bar — airspace timer, vault count, contextual hints."""

from textual.reactive import reactive
from textual.widgets import Static

from password_manager.tui.theme import ICONS


class StatusBar(Static):
    """Bottom status bar with live session countdown and vault stats."""

    DEFAULT_CSS = ""

    time_remaining: reactive[int] = reactive(0)
    entry_count: reactive[int] = reactive(0)
    airspace_open: reactive[bool] = reactive(False)

    def __init__(self, **kwargs) -> None:
        super().__init__(markup=False, **kwargs)

    def render(self) -> str:
        # Airspace indicator
        if self.airspace_open:
            minutes = self.time_remaining // 60
            seconds = self.time_remaining % 60
            time_str = f"{minutes:02d}:{seconds:02d}"
            airspace = f"{ICONS['airspace_open']} AIRSPACE {time_str}"
        else:
            airspace = f"{ICONS['airspace_closed']} AIRSPACE CLOSED"

        # Vault count
        vault = f"{self.entry_count} entries"

        # Hints (square brackets are literal, not Rich markup)
        hints = "[/]search  [c]opy  [?]help  [q]uit"

        return f"  {airspace}  {ICONS['block_full']}  {vault}  {ICONS['block_full']}  {hints}"
