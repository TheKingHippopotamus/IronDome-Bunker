"""Re-authentication modal — used before destructive actions like delete.

Dismisses with True when re-auth succeeds, False when cancelled.
Supports password verification (always) and biometric (when available).
"""

import logging

from textual.screen import ModalScreen
from textual.widgets import Static, Input, Button, LoadingIndicator
from textual.containers import Center, Vertical, Horizontal
from textual import work

from password_manager.tui.theme import ICONS

log = logging.getLogger("IronDome.TUI.ReAuth")


class ReAuthModal(ModalScreen[bool]):
    """Modal re-authentication prompt before sensitive destructive actions.

    Always offers password entry. If the current auth mode includes biometric,
    also shows a biometric option — biometric failure falls through to password.
    Dismisses with True on successful verification, False on cancel.
    """

    DEFAULT_CSS = ""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, app_state, action_label: str = "Delete", **kwargs) -> None:
        super().__init__(**kwargs)
        self._state = app_state
        self._action_label = action_label
        self._auth_mode = app_state.get_auth_mode()
        self._bio_option = self._auth_mode in ("biometric_only", "biometric_password")

    def compose(self):
        with Center():
            with Vertical(id="reauth-box"):
                yield Static(
                    f"{ICONS['warning']}  Re-authenticate to {self._action_label}",
                    id="reauth-title",
                )
                yield Static(
                    "This action requires identity verification.",
                    id="reauth-subtitle",
                )
                yield Static("", id="reauth-status")
                yield Input(
                    placeholder="Master password",
                    password=True,
                    id="reauth-password",
                )
                yield Center(LoadingIndicator(id="reauth-spinner", classes="hidden"))
                yield Static("", id="reauth-error")
                with Horizontal(id="reauth-actions"):
                    if self._bio_option:
                        yield Button(
                            f"{ICONS['shield']} Biometric",
                            variant="primary",
                            id="btn-reauth-bio",
                        )
                    yield Button(
                        f"{ICONS['locked']} Password",
                        variant="primary" if not self._bio_option else "default",
                        id="btn-reauth-pw",
                    )
                    yield Button("Cancel", id="btn-reauth-cancel")

    def on_mount(self) -> None:
        if self._bio_option:
            self.query_one("#reauth-status").update(
                "Use biometric or enter master password below."
            )
        try:
            self.query_one("#reauth-password", Input).focus()
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-reauth-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-reauth-bio":
            self._run_bio_verify()
        elif event.button.id == "btn-reauth-pw":
            self._run_password_verify()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "reauth-password":
            self._run_password_verify()

    @work(thread=True)
    def _run_bio_verify(self) -> None:
        self.app.call_from_thread(self._show_spinner, True)
        self.app.call_from_thread(self._clear_error)
        try:
            result = self._state.authenticate_biometric()
            self.app.call_from_thread(self._on_bio_result, result)
        except Exception as exc:
            log.error("Bio re-auth error: %s", exc)
            self.app.call_from_thread(self._show_error, f"Biometric error: {exc}")
            self.app.call_from_thread(self._show_spinner, False)

    def _on_bio_result(self, success: bool) -> None:
        self._show_spinner(False)
        if success:
            self.dismiss(True)
        else:
            self._show_error(
                f"{ICONS['cross']}  Biometric failed. Enter master password to continue."
            )
            try:
                self.query_one("#reauth-password", Input).focus()
            except Exception:
                pass

    @work(thread=True)
    def _run_password_verify(self) -> None:
        self.app.call_from_thread(self._show_spinner, True)
        self.app.call_from_thread(self._clear_error)
        try:
            password = self.query_one("#reauth-password", Input).value
            if not password:
                self.app.call_from_thread(self._show_error, "Password is required.")
                self.app.call_from_thread(self._show_spinner, False)
                return
            result = self._state.verify_password(password)
            self.app.call_from_thread(self._on_password_result, result)
        except Exception as exc:
            log.error("Password re-auth error: %s", exc)
            self.app.call_from_thread(self._show_error, f"Verification error: {exc}")
            self.app.call_from_thread(self._show_spinner, False)

    def _on_password_result(self, success: bool) -> None:
        self._show_spinner(False)
        if success:
            self.dismiss(True)
        else:
            self._show_error("Incorrect password. Action cancelled.")
            try:
                pw_input = self.query_one("#reauth-password", Input)
                pw_input.value = ""
                pw_input.focus()
            except Exception:
                pass

    def _show_error(self, msg: str) -> None:
        try:
            self.query_one("#reauth-error").update(f"{ICONS['cross']}  {msg}")
        except Exception:
            pass

    def _clear_error(self) -> None:
        try:
            self.query_one("#reauth-error").update("")
        except Exception:
            pass

    def _show_spinner(self, show: bool) -> None:
        try:
            spinner = self.query_one("#reauth-spinner")
            if show:
                spinner.remove_class("hidden")
            else:
                spinner.add_class("hidden")
        except Exception:
            pass

    def action_cancel(self) -> None:
        self.dismiss(False)
