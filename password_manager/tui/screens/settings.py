"""Settings screen — toggle switches and sliders for preferences."""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Switch, Button, Label
from textual.containers import Vertical, Horizontal

from password_manager.tui.theme import ICONS
from password_manager.tui.widgets.status_bar import StatusBar


class SettingsScreen(Screen):
    """Interactive settings with toggles and numeric inputs."""

    DEFAULT_CSS = ""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, app_state, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state = app_state

    def compose(self):
        yield Header()
        yield Static(
            f"  {ICONS['dome_active']} SETTINGS",
            id="settings-title",
        )

        with Vertical(id="settings-body"):
            # Password length
            with Horizontal(classes="setting-row"):
                yield Label("Password length:", classes="setting-label")
                yield Input(
                    value=str(self._state.settings.get("password_length", 20)),
                    id="set-pw-length",
                    type="integer",
                    classes="setting-input",
                )

            # Special characters
            with Horizontal(classes="setting-row"):
                yield Label("Special characters:", classes="setting-label")
                yield Switch(
                    value=self._state.settings.get("use_special_chars", True),
                    id="set-special",
                )

            # Uppercase
            with Horizontal(classes="setting-row"):
                yield Label("Uppercase letters:", classes="setting-label")
                yield Switch(
                    value=self._state.settings.get("use_uppercase", True),
                    id="set-uppercase",
                )

            # Digits
            with Horizontal(classes="setting-row"):
                yield Label("Include digits:", classes="setting-label")
                yield Switch(
                    value=self._state.settings.get("use_digits", True),
                    id="set-digits",
                )

            # Session timeout
            with Horizontal(classes="setting-row"):
                yield Label("Session timeout (minutes):", classes="setting-label")
                yield Input(
                    value=str(self._state.settings.get("session_timeout", 1800) // 60),
                    id="set-timeout",
                    type="integer",
                    classes="setting-input",
                )

            # Show strength
            with Horizontal(classes="setting-row"):
                yield Label("Show password strength:", classes="setting-label")
                yield Switch(
                    value=self._state.settings.get("show_strength", True),
                    id="set-strength",
                )

            with Horizontal(id="settings-actions"):
                yield Button("Save", variant="primary", id="btn-save-settings")
                yield Button("Reset Defaults", id="btn-reset")
                yield Button("Back", id="btn-back")

        yield StatusBar()
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save-settings":
            self._save_settings()
        elif event.button.id == "btn-reset":
            self._state.settings.reset()
            self.notify("Settings reset to defaults", timeout=3)
            self.app.pop_screen()
        elif event.button.id == "btn-back":
            self.action_go_back()

    def _save_settings(self) -> None:
        settings = self._state.settings

        try:
            length = int(self.query_one("#set-pw-length", Input).value)
            if 4 <= length <= 200:
                settings.set("password_length", length)
        except ValueError:
            pass

        settings.set("use_special_chars", self.query_one("#set-special", Switch).value)
        settings.set("use_uppercase", self.query_one("#set-uppercase", Switch).value)
        settings.set("use_digits", self.query_one("#set-digits", Switch).value)
        settings.set("show_strength", self.query_one("#set-strength", Switch).value)

        try:
            timeout_min = int(self.query_one("#set-timeout", Input).value)
            if 1 <= timeout_min <= 480:
                settings.set("session_timeout", timeout_min * 60)
        except ValueError:
            pass

        self.notify("Settings saved", timeout=3)

    def action_go_back(self) -> None:
        self.app.pop_screen()
