"""Save screen — form for creating a new vault entry."""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button
from textual.containers import Vertical, Horizontal

from password_manager.tui.theme import ICONS
from password_manager.tui.widgets.status_bar import StatusBar


class SaveScreen(Screen):
    """Form for saving a new password entry to the vault."""

    DEFAULT_CSS = """
    SaveScreen {
        layout: vertical;
    }

    #save-title {
        dock: top;
        height: 1;
        background: #0D1117;
        color: #00FF41;
        text-style: bold;
        padding: 0 2;
    }

    #save-body {
        margin: 2 4;
        height: 1fr;
    }

    .form-row {
        height: auto;
        margin-bottom: 1;
    }

    .form-label {
        color: #94A3B8;
        margin-bottom: 0;
    }

    #save-error {
        color: #FF2020;
        height: auto;
        margin-top: 1;
    }

    #save-actions {
        layout: horizontal;
        height: auto;
        margin: 2 0;
        align: center middle;
    }

    #save-actions Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, app_state, prefill_password: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._state = app_state
        self._prefill_password = prefill_password

    def compose(self):
        yield Header()
        yield Static(
            f"  {ICONS['dome_active']} NEW BUNKER ENTRY",
            id="save-title",
        )

        with Vertical(id="save-body"):
            with Vertical(classes="form-row"):
                yield Static("Service / Website *", classes="form-label")
                yield Input(placeholder="github.com", id="save-website")

            with Vertical(classes="form-row"):
                yield Static("Username *", classes="form-label")
                yield Input(placeholder="user@example.com", id="save-username")

            with Vertical(classes="form-row"):
                yield Static("Password *", classes="form-label")
                yield Input(
                    placeholder="Enter or generate password",
                    password=True,
                    value=self._prefill_password,
                    id="save-password",
                )

            with Vertical(classes="form-row"):
                yield Static("Notes (optional)", classes="form-label")
                yield Input(placeholder="Additional notes...", id="save-notes")

            yield Static("", id="save-error")

            with Horizontal(id="save-actions"):
                yield Button("Save Entry", variant="primary", id="btn-save")
                yield Button("Generate Password", id="btn-generate")
                yield Button("Cancel", id="btn-cancel")

        yield StatusBar()
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self._save()
        elif event.button.id == "btn-generate":
            from password_manager.tui.screens.generator import GeneratorScreen
            self.app.push_screen(GeneratorScreen(self._state))
        elif event.button.id == "btn-cancel":
            self.action_go_back()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # Tab through fields on Enter, save on last field
        if event.input.id == "save-website":
            self.query_one("#save-username", Input).focus()
        elif event.input.id == "save-username":
            self.query_one("#save-password", Input).focus()
        elif event.input.id == "save-password":
            self.query_one("#save-notes", Input).focus()
        elif event.input.id == "save-notes":
            self._save()

    def _save(self) -> None:
        website = self.query_one("#save-website", Input).value.strip()
        username = self.query_one("#save-username", Input).value.strip()
        password = self.query_one("#save-password", Input).value
        notes = self.query_one("#save-notes", Input).value.strip()

        # Validate
        if not website:
            self._show_error("Service/website is required.")
            self.query_one("#save-website", Input).focus()
            return
        if not username:
            self._show_error("Username is required.")
            self.query_one("#save-username", Input).focus()
            return
        if not password:
            self._show_error("Password is required.")
            self.query_one("#save-password", Input).focus()
            return

        if self._state.save_entry(username, website, password, notes):
            self.notify(f"Entry saved for {username} at {website}", timeout=3)
            self.app.pop_screen()
        else:
            self._show_error("Failed to save entry.")

    def _show_error(self, msg: str) -> None:
        self.query_one("#save-error").update(f"{ICONS['cross']}  {msg}")

    def action_go_back(self) -> None:
        self.app.pop_screen()
