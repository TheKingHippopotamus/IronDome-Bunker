"""Password generator screen — live preview with strength meter."""

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

    DEFAULT_CSS = """
    GeneratorScreen {
        layout: vertical;
    }

    #gen-title {
        dock: top;
        height: 1;
        background: #0D1117;
        color: #00FF41;
        text-style: bold;
        padding: 0 2;
    }

    #gen-body {
        margin: 2 4;
        height: 1fr;
    }

    #gen-output {
        color: #00FF41;
        text-style: bold;
        text-align: center;
        padding: 2;
        margin: 1 0;
        background: #1A1F24;
        border: solid #1E2D3D;
        height: 5;
        content-align: center middle;
    }

    #gen-controls {
        margin: 1 0;
    }

    .control-row {
        layout: horizontal;
        height: 3;
        margin-bottom: 1;
        align: left middle;
    }

    .control-label {
        width: 24;
        color: #94A3B8;
        padding: 1 1;
    }

    .control-value {
        width: auto;
        padding: 1 1;
    }

    #gen-length-input {
        width: 10;
    }

    #gen-actions {
        layout: horizontal;
        height: auto;
        margin: 2 0;
        align: center middle;
    }

    #gen-actions Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("r", "regenerate", "Regenerate"),
        ("c", "copy_password", "Copy"),
        ("s", "save_password", "Save"),
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
                yield Button("[r] Regenerate", variant="primary", id="btn-regen")
                yield Button("[c] Copy", id="btn-copy")
                yield Button("[s] Save as Entry", id="btn-save")

        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        self._generate()

    def _generate(self) -> None:
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
