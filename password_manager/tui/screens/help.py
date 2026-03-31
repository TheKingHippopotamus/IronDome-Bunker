"""Help overlay — keyboard shortcuts and navigation reference."""

from textual.screen import ModalScreen
from textual.widgets import Static
from textual.containers import Center, Vertical

from password_manager.tui.theme import ICONS


HELP_TEXT = """\
[bold #00FF41]IRONDOME KEYBOARD SHORTCUTS[/]

[bold #94A3B8]NAVIGATION[/]
  [#00B4D8]Up / Down[/]        Move between items
  [#00B4D8]Left[/]             Go back
  [#00B4D8]Right[/]            Open / enter
  [#00B4D8]Tab / Shift+Tab[/]  Next / previous panel
  [#00B4D8]Enter[/]            Confirm / open selected
  [#00B4D8]Esc[/]              Back / cancel
  [#00B4D8]Space[/]            Toggle (reveal password, switch)

[bold #94A3B8]DASHBOARD[/]
  [#00B4D8]1[/]           Vault (browse & search)
  [#00B4D8]2[/]           Generator
  [#00B4D8]3[/]           New Entry
  [#00B4D8]4[/]           Fortify (backup)
  [#00B4D8]5[/]           Settings
  [#00B4D8]q[/]           Logout

[bold #94A3B8]VAULT[/]
  [#00B4D8]/[/]           Search (fuzzy filter)
  [#00B4D8]Enter / Right[/]  Open entry
  [#00B4D8]c[/]           Copy password (clears in 30s)
  [#00B4D8]u[/]           Copy username
  [#00B4D8]n[/]           New entry
  [#00B4D8]Ctrl+D[/]      Delete
  [#00B4D8]Left / Esc[/]  Back

[bold #94A3B8]ENTRY DETAIL[/]
  [#00B4D8]Space[/]       Show/hide password (10s auto-hide)
  [#00B4D8]c[/]           Copy password
  [#00B4D8]u[/]           Copy username
  [#00B4D8]Click field[/] Copy value
  [#00B4D8]Ctrl+D[/]      Delete
  [#00B4D8]Left / Esc[/]  Back

[bold #94A3B8]GENERATOR[/]
  [#00B4D8]r[/]           Regenerate
  [#00B4D8]c[/]           Copy
  [#00B4D8]s[/]           Save as entry

[bold #94A3B8]GLOBAL[/]
  [#00B4D8]Ctrl+Q[/]      Quit
  [#00B4D8]Ctrl+L[/]      Lock vault
  [#00B4D8]?[/]           This help

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
