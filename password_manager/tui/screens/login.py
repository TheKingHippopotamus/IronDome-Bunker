"""Login screen — handles all three auth modes."""

from textual.screen import Screen
from textual.widgets import Static, Input, Button, LoadingIndicator
from textual.containers import Center, Vertical, Horizontal
from textual import work

from password_manager.tui.theme import ICONS, LOGO_SMALL
from password_manager.tui.state.events import AuthSuccess, AuthFailed


class LoginScreen(Screen):
    """Authentication screen supporting biometric, password, and dual-factor modes."""

    DEFAULT_CSS = """
    LoginScreen {
        align: center middle;
    }

    #login-box {
        width: 60;
        height: auto;
        background: #111518;
        border: solid #1E2D3D;
        padding: 2 4;
    }

    #login-header {
        color: #00FF41;
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    #login-auth-mode {
        color: #94A3B8;
        text-align: center;
        width: 100%;
        margin-bottom: 2;
    }

    #login-bio-status {
        color: #94A3B8;
        text-align: center;
        width: 100%;
        height: 3;
        margin-bottom: 1;
    }

    #login-username {
        margin-bottom: 1;
    }

    #login-password {
        margin-bottom: 1;
    }

    #login-error {
        color: #FF2020;
        text-align: center;
        width: 100%;
        height: auto;
        margin-top: 1;
    }

    #login-actions {
        layout: horizontal;
        align: center middle;
        height: auto;
        margin-top: 2;
    }

    #login-actions Button {
        margin: 0 1;
    }

    #login-spinner {
        height: 3;
        margin: 1 0;
    }

    .hidden {
        display: none;
    }
    """

    BINDINGS = [
        ("escape", "quit_app", "Quit"),
    ]

    def __init__(self, app_state, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state = app_state
        self._auth_mode = None

    def compose(self):
        with Center():
            with Vertical(id="login-box"):
                yield Static(
                    f"{LOGO_SMALL}  AUTHENTICATION",
                    id="login-header",
                )
                yield Static("Detecting security level...", id="login-auth-mode")

                # Biometric status area
                yield Static("", id="login-bio-status")

                # Credential inputs (shown for password modes)
                yield Input(placeholder="Username", id="login-username", classes="hidden")
                yield Input(
                    placeholder="Master password",
                    password=True,
                    id="login-password",
                    classes="hidden",
                )

                # Loading spinner
                yield Center(LoadingIndicator(id="login-spinner", classes="hidden"))

                # Error display
                yield Static("", id="login-error")

                # Action buttons
                with Horizontal(id="login-actions"):
                    yield Button("Unlock Vault", variant="primary", id="btn-unlock")
                    yield Button("Quit", id="btn-quit")

    def on_mount(self) -> None:
        self._detect_auth_mode()

    def _detect_auth_mode(self) -> None:
        if not self._state.is_configured:
            self.query_one("#login-auth-mode").update("No vault configured. Run 'irondome create bunker' first.")
            self.query_one("#btn-unlock").disabled = True
            return

        self._auth_mode = self._state.get_auth_mode()
        mode_display = {
            "biometric_only": f"{ICONS['shield']}  BIOMETRIC ONLY",
            "biometric_password": f"{ICONS['shield']}  BIOMETRIC + PASSWORD",
            "password_only": f"{ICONS['locked']}  PASSWORD ONLY",
        }
        self.query_one("#login-auth-mode").update(
            mode_display.get(self._auth_mode, "STANDARD AUTH")
        )

        if self._auth_mode in ("biometric_only", "biometric_password"):
            self.query_one("#login-bio-status").update(
                f"Biometric authentication will be requested."
            )
        if self._auth_mode in ("biometric_password", "password_only", None):
            self.query_one("#login-username").remove_class("hidden")
            self.query_one("#login-password").remove_class("hidden")
            if self._auth_mode == "biometric_password":
                self.query_one("#login-username").add_class("hidden")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-quit":
            self.app.exit()
        elif event.button.id == "btn-unlock":
            self._attempt_auth()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id in ("login-username", "login-password"):
            self._attempt_auth()

    def _attempt_auth(self) -> None:
        self._show_spinner(True)
        self._clear_error()

        if self._auth_mode in ("biometric_only", "biometric_password"):
            self._run_biometric_auth()
        else:
            self._run_password_auth()

    @work(thread=True)
    def _run_biometric_auth(self) -> None:
        """Run biometric auth in a thread to avoid blocking the UI."""
        result = self._state.authenticate_biometric()
        self.app.call_from_thread(self._on_auth_result, result)

    @work(thread=True)
    def _run_password_auth(self) -> None:
        """Run password auth in a thread."""
        username = self.query_one("#login-username", Input).value.strip()
        password = self.query_one("#login-password", Input).value

        if not password:
            self.app.call_from_thread(self._show_error, "Password is required.")
            self.app.call_from_thread(self._show_spinner, False)
            return

        result = self._state.authenticate_password(username, password)
        self.app.call_from_thread(self._on_auth_result, result)

    def _on_auth_result(self, success: bool) -> None:
        self._show_spinner(False)
        if success:
            self.post_message(AuthSuccess(self._state.username or "user"))
        else:
            self._show_error("Authentication failed. Check credentials and try again.")

    def _show_error(self, msg: str) -> None:
        self.query_one("#login-error").update(f"{ICONS['cross']}  {msg}")

    def _clear_error(self) -> None:
        self.query_one("#login-error").update("")

    def _show_spinner(self, show: bool) -> None:
        spinner = self.query_one("#login-spinner")
        if show:
            spinner.remove_class("hidden")
        else:
            spinner.add_class("hidden")

    def action_quit_app(self) -> None:
        self.app.exit()
