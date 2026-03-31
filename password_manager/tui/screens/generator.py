"""Password generator screen — live preview with strength meter."""

from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button, Switch, Label
from textual.containers import Vertical, Horizontal

from password_manager.tui.theme import ICONS
from password_manager.tui.widgets.strength_meter import StrengthMeter
from password_manager.tui.widgets.status_bar import StatusBar
from password_manager.tui.security.clipboard import copy_with_auto_clear
from password_manager.generator import generate_password


class GeneratorScreen(Screen):
    """Interactive password generator with real-time preview."""

    DEFAULT_CSS = ""

    BINDINGS = [
        Binding("r", "regenerate", "r: Regenerate", show=True),
        Binding("c", "copy_password", "c: Copy", show=True),
        Binding("s", "save_password", "s: Save Entry", show=True),
        Binding("escape", "go_back", "Esc: Back", show=True),
        Binding("down", "focus_next", show=False),
        Binding("up", "focus_previous", show=False),
    ]

    def __init__(self, app_state, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state = app_state
        self._current_password = ""

    def compose(self):
        yield Header()
        yield Static(
            f"  {ICONS['dome_active']} PASSWORD GENERATOR",
            id="gen-title",
        )

        with Vertical(id="gen-body"):
            yield Static("Generating...", id="gen-output")
            yield StrengthMeter(id="gen-strength")

            with Vertical(id="gen-controls"):
                with Horizontal(classes="control-row"):
                    yield Label("Password length:", classes="control-label")
                    yield Input(
                        value=str(self._state.settings.get("password_length", 20)),
                        id="gen-length-input",
                        type="integer",
                    )

                with Horizontal(classes="control-row"):
                    yield Label("Special characters:", classes="control-label")
                    yield Switch(
                        value=self._state.settings.get("use_special_chars", True),
                        id="gen-special",
                    )

                with Horizontal(classes="control-row"):
                    yield Label("Uppercase letters:", classes="control-label")
                    yield Switch(
                        value=self._state.settings.get("use_uppercase", True),
                        id="gen-uppercase",
                    )

                with Horizontal(classes="control-row"):
                    yield Label("Include digits:", classes="control-label")
                    yield Switch(
                        value=self._state.settings.get("use_digits", True),
                        id="gen-digits",
                    )

            with Horizontal(id="gen-actions"):
                yield Button("\\[r] Regenerate", variant="primary", id="btn-regen")
                yield Button("\\[c] Copy", id="btn-copy")
                yield Button("\\[s] Save as Entry", id="btn-save")

        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        self._generate()

    def _generate(self) -> None:
        try:
            try:
                length = int(self.query_one("#gen-length-input", Input).value)
                length = max(4, min(200, length))
            except (ValueError, TypeError):
                length = 20

            use_special = self.query_one("#gen-special", Switch).value
            use_uppercase = self.query_one("#gen-uppercase", Switch).value
            use_digits = self.query_one("#gen-digits", Switch).value

            result = generate_password(
                length=length,
                use_special=use_special,
                use_uppercase=use_uppercase,
                use_digits=use_digits,
            )

            if result:
                self._current_password = result["password"]
                self.query_one("#gen-output").update(result["password"])
                meter = self.query_one("#gen-strength", StrengthMeter)
                meter.strength = result["strength"]
        except Exception as exc:
            self.notify(f"Generation failed: {exc}", severity="error", timeout=3)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        self._generate()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "gen-length-input":
            self._generate()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-regen":
            self.action_regenerate()
        elif event.button.id == "btn-copy":
            self.action_copy_password()
        elif event.button.id == "btn-save":
            self.action_save_password()

    def action_focus_next(self) -> None:
        self.focus_next()

    def action_focus_previous(self) -> None:
        self.focus_previous()

    def action_regenerate(self) -> None:
        self._generate()

    def action_copy_password(self) -> None:
        if self._current_password:
            timeout = self._state.settings.get("clipboard_timeout", 30)
            if copy_with_auto_clear(self._current_password, timeout=timeout):
                self.notify(f"Password copied — clears in {timeout}s", timeout=3)

    def action_save_password(self) -> None:
        if self._current_password:
            from password_manager.tui.screens.save import SaveScreen
            self.app.push_screen(
                SaveScreen(self._state, prefill_password=self._current_password)
            )

    def action_go_back(self) -> None:
        self.app.pop_screen()
