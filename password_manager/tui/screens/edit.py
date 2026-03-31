"""Edit screen — modify an existing vault entry."""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button
from textual.containers import Vertical, Horizontal
from textual.binding import Binding

from password_manager.tui.theme import ICONS
from password_manager.tui.widgets.status_bar import StatusBar
from password_manager.generator import generate_password


class EditScreen(Screen):
    """Form for editing an existing vault entry."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("down", "focus_next", "Next Field", show=False),
        Binding("up", "focus_previous", "Prev Field", show=False),
    ]

    def __init__(self, app_state, entry: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state = app_state
        self._entry = entry
        # Store originals for deletion of old entry if keys change
        self._orig_username = entry.get("username", "")
        self._orig_website = entry.get("website", "")

    def compose(self):
        yield Header()
        yield Static(
            f"  {ICONS['dome_active']} EDIT BUNKER ENTRY",
            id="save-title",
        )

        with Vertical(id="save-body"):
            with Vertical(classes="form-row"):
                yield Static("Service / Website *", classes="form-label")
                yield Input(
                    value=self._entry.get("website", ""),
                    placeholder="github.com",
                    id="edit-website",
                )

            with Vertical(classes="form-row"):
                yield Static("Username *", classes="form-label")
                yield Input(
                    value=self._entry.get("username", ""),
                    placeholder="user@example.com",
                    id="edit-username",
                )

            with Vertical(classes="form-row"):
                yield Static("Password *", classes="form-label")
                with Horizontal(classes="password-row"):
                    yield Input(
                        value=self._entry.get("password", ""),
                        placeholder="Enter or generate password",
                        password=True,
                        id="edit-password",
                    )
                    yield Button("Generate", id="btn-generate-inline")

            with Vertical(classes="form-row"):
                yield Static("Notes (optional)", classes="form-label")
                yield Input(
                    value=self._entry.get("notes", ""),
                    placeholder="Additional notes...",
                    id="edit-notes",
                )

            yield Static("", id="save-error")

            with Horizontal(id="save-actions"):
                yield Button("Save Changes", variant="primary", id="btn-save")
                yield Button("Cancel", id="btn-cancel")

        yield StatusBar()
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self._save()
        elif event.button.id == "btn-generate-inline":
            self._generate_inline()
        elif event.button.id == "btn-cancel":
            self.action_go_back()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "edit-website":
            self.query_one("#edit-username", Input).focus()
        elif event.input.id == "edit-username":
            self.query_one("#edit-password", Input).focus()
        elif event.input.id == "edit-password":
            self.query_one("#edit-notes", Input).focus()
        elif event.input.id == "edit-notes":
            self._save()

    def _generate_inline(self) -> None:
        try:
            length = self._state.settings.get("password_length", 20)
            use_special = self._state.settings.get("use_special_chars", True)
            use_uppercase = self._state.settings.get("use_uppercase", True)
            use_digits = self._state.settings.get("use_digits", True)

            result = generate_password(
                length=length,
                use_special=use_special,
                use_uppercase=use_uppercase,
                use_digits=use_digits,
            )

            if result:
                pw_input = self.query_one("#edit-password", Input)
                pw_input.value = result["password"]
                self.notify(
                    f"Generated {result['strength']} password ({length} chars)",
                    timeout=3,
                )
        except Exception as exc:
            self.notify(f"Generation failed: {exc}", severity="error", timeout=3)

    def _save(self) -> None:
        website = self.query_one("#edit-website", Input).value.strip()
        username = self.query_one("#edit-username", Input).value.strip()
        password = self.query_one("#edit-password", Input).value
        notes = self.query_one("#edit-notes", Input).value.strip()

        if not website:
            self._show_error("Service/website is required.")
            self.query_one("#edit-website", Input).focus()
            return
        if not username:
            self._show_error("Username is required.")
            self.query_one("#edit-username", Input).focus()
            return
        if not password:
            self._show_error("Password is required.")
            self.query_one("#edit-password", Input).focus()
            return

        try:
            updated = self._state.update_entry(
                self._orig_username,
                self._orig_website,
                username,
                website,
                password,
                notes,
            )
            if updated:
                self.dismiss(updated)
            else:
                self._show_error("Failed to save changes.")
        except Exception as exc:
            self._show_error(f"Save error: {exc}")

    def _show_error(self, msg: str) -> None:
        try:
            self.query_one("#save-error").update(f"{ICONS['cross']}  {msg}")
        except Exception:
            pass

    def action_focus_next(self) -> None:
        self.focus_next()

    def action_focus_previous(self) -> None:
        self.focus_previous()

    def action_go_back(self) -> None:
        self.dismiss(None)
