"""Detail screen — view a single vault entry with reveal/copy/delete."""

from typing import Optional

from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button
from textual.containers import Vertical, Horizontal
from textual.timer import Timer

from password_manager.tui.theme import ICONS
from password_manager.tui.widgets.strength_meter import StrengthMeter
from password_manager.tui.widgets.status_bar import StatusBar
from password_manager.tui.security.clipboard import copy_with_auto_clear
from password_manager.generator import calculate_password_strength


class DetailScreen(Screen):
    """View details of a single vault entry."""

    DEFAULT_CSS = ""

    BINDINGS = [
        Binding("c", "copy_password", "c: Copy Pass", show=True),
        Binding("u", "copy_username", "u: Copy User", show=True),
        Binding("space", "toggle_reveal", "Space: Reveal", show=True),
        Binding("ctrl+d", "delete_entry", "^D: Delete", show=True),
        Binding("escape", "go_back", "Esc: Back", show=True),
        Binding("down", "focus_next", show=False),
        Binding("up", "focus_previous", show=False),
        Binding("left", "go_back", show=False),
    ]

    def __init__(self, app_state, entry: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state = app_state
        self._entry = entry
        self._revealed = False
        self._reveal_timer: Optional[Timer] = None
        self._reveal_countdown = 0

    def compose(self):
        yield Header()
        yield Static(
            f"  {ICONS['dome_active']} BUNKER DETAIL",
            id="detail-title",
        )

        with Vertical(id="detail-body"):
            # Service
            with Horizontal(classes="field-row"):
                yield Static("Service", classes="field-label")
                yield Static(self._entry.get("website", ""), classes="field-value")

            # Username — click to copy
            with Horizontal(classes="field-row"):
                yield Static("Username", classes="field-label")
                yield Button(
                    self._entry.get("username", ""),
                    classes="field-value field-copy-btn",
                    id="username-value",
                )

            # Password (masked by default) — click to copy the actual password
            with Horizontal(classes="field-row"):
                yield Static("Password", classes="field-label")
                yield Button(
                    "\u2022" * 12,
                    classes="field-value field-copy-btn",
                    id="password-value",
                )
                yield Static("", id="reveal-timer")

            # Strength
            with Horizontal(classes="field-row"):
                yield Static("Strength", classes="field-label")
                yield StrengthMeter(id="strength-display")

            # Notes
            if self._entry.get("notes"):
                with Horizontal(classes="field-row"):
                    yield Static("Notes", classes="field-label")
                    yield Static(self._entry.get("notes", ""), classes="field-value")

            # Created
            with Horizontal(classes="field-row"):
                yield Static("Created", classes="field-label")
                yield Static(self._entry.get("created_at", ""), classes="field-value")

        # Action buttons
        with Horizontal(id="detail-actions"):
            yield Button("\\[c] Copy Password", variant="primary", id="btn-copy-pw")
            yield Button("\\[u] Copy Username", id="btn-copy-user")
            yield Button("\\[Space] Reveal", id="btn-reveal")
            yield Button("\\[Ctrl+D] Delete", variant="error", id="btn-delete")

        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        strength = calculate_password_strength(self._entry.get("password", ""))
        meter = self.query_one("#strength-display", StrengthMeter)
        meter.strength = strength

    def on_button_pressed(self, event: Button.Pressed) -> None:
        actions = {
            "btn-copy-pw": self.action_copy_password,
            "btn-copy-user": self.action_copy_username,
            "btn-reveal": self.action_toggle_reveal,
            "btn-delete": self.action_delete_entry,
            # Inline click-to-copy field buttons
            "username-value": self.action_copy_username,
            "password-value": self.action_copy_password,
        }
        action = actions.get(event.button.id)
        if action:
            action()

    def action_focus_next(self) -> None:
        self.focus_next()

    def action_focus_previous(self) -> None:
        self.focus_previous()

    def action_go_back(self) -> None:
        self._hide_password()
        self.app.pop_screen()

    def action_copy_password(self) -> None:
        timeout = self._state.settings.get("clipboard_timeout", 30)
        if copy_with_auto_clear(self._entry["password"], timeout=timeout):
            self.notify(f"Copied! Clears in {timeout}s", timeout=3)

    def action_copy_username(self) -> None:
        if copy_with_auto_clear(self._entry["username"], timeout=0):
            self.notify("Copied!", timeout=3)

    def action_toggle_reveal(self) -> None:
        if self._revealed:
            self._hide_password()
        else:
            self._show_password()

    def _show_password(self) -> None:
        try:
            self._revealed = True
            self._reveal_countdown = 10
            pw_widget = self.query_one("#password-value", Button)
            pw_widget.label = self._entry.get("password", "")
            pw_widget.styles.color = "#00FF41"
            self._update_reveal_timer()
            self._reveal_timer = self.set_interval(1.0, self._tick_reveal)
        except Exception:
            pass

    def _hide_password(self) -> None:
        try:
            self._revealed = False
            if self._reveal_timer:
                self._reveal_timer.stop()
                self._reveal_timer = None
            pw_widget = self.query_one("#password-value", Button)
            pw_widget.label = "\u2022" * 12
            pw_widget.styles.color = "#4A5568"
            self.query_one("#reveal-timer").update("")
        except Exception:
            self._revealed = False

    def _tick_reveal(self) -> None:
        try:
            self._reveal_countdown -= 1
            if self._reveal_countdown <= 0:
                self._hide_password()
            else:
                self._update_reveal_timer()
        except Exception:
            self._hide_password()

    def _update_reveal_timer(self) -> None:
        try:
            self.query_one("#reveal-timer").update(f"hiding in {self._reveal_countdown}s")
        except Exception:
            pass

    def action_delete_entry(self) -> None:
        from password_manager.tui.screens.confirm import ConfirmDialog
        self.app.push_screen(
            ConfirmDialog(
                f"Delete {self._entry['username']} at {self._entry['website']}?",
                action_label="Delete",
                danger=True,
            ),
            callback=self._do_delete,
        )

    def _do_delete(self, confirmed: bool) -> None:
        if confirmed:
            if self._state.delete_entry(self._entry["username"], self._entry["website"]):
                self.notify("Entry deleted", timeout=3)
                self.app.pop_screen()
            else:
                self.notify("Delete failed", severity="error", timeout=3)
