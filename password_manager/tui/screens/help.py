"""Help overlay — keyboard shortcuts and navigation reference."""

from textual.screen import ModalScreen
from textual.widgets import Static
from textual.containers import Center, Vertical

from password_manager.tui.theme import ICONS


HELP_TEXT = """\
[bold #00FF41]IRONDOME KEYBOARD SHORTCUTS[/]

[bold #94A3B8]GLOBAL[/]
  [#00B4D8]?[/]           Help (this screen)
  [#00B4D8]Ctrl+P[/]      Command palette
  [#00B4D8]q[/]           Quit / close panel
  [#00B4D8]Esc[/]         Back / cancel
  [#00B4D8]/[/]           Search / filter
  [#00B4D8]Tab[/]         Next panel
  [#00B4D8]Ctrl+L[/]      Lock vault

[bold #94A3B8]NAVIGATION[/]
  [#00B4D8]j / Down[/]    Move down
  [#00B4D8]k / Up[/]      Move up
  [#00B4D8]g / Home[/]    Jump to top
  [#00B4D8]G / End[/]     Jump to bottom

[bold #94A3B8]ENTRY ACTIONS[/]
  [#00B4D8]Enter[/]       Open / view detail
  [#00B4D8]c[/]           Copy password (auto-clears)
  [#00B4D8]u[/]           Copy username
  [#00B4D8]Space[/]       Reveal password (10s)
  [#00B4D8]n[/]           New entry
  [#00B4D8]Ctrl+D[/]      Delete entry

[bold #94A3B8]DASHBOARD[/]
  [#00B4D8]1[/]           Vault list
  [#00B4D8]2[/]           Search
  [#00B4D8]3[/]           Password generator
  [#00B4D8]4[/]           Save new entry
  [#00B4D8]5[/]           Backup / Fortify
  [#00B4D8]6[/]           Settings

[#4A5568]Press any key to close[/]\
"""


class HelpOverlay(ModalScreen):
    """Full help overlay with all keyboard shortcuts."""

    DEFAULT_CSS = ""

    def compose(self):
        with Center():
            with Vertical(id="help-box"):
                yield Static(HELP_TEXT, markup=True)

    def on_key(self, event) -> None:
        self.dismiss()
