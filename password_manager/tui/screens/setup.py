"""SetupScreen — first-time vault creation flow."""

from __future__ import annotations

import logging
from typing import Optional

from textual.screen import Screen
from textual.widgets import Static, Input, Button, LoadingIndicator, RadioButton, RadioSet
from textual.containers import Center, Vertical, Horizontal
from textual import work

from password_manager.tui.theme import ICONS, LOGO_SMALL
from password_manager.tui.state.events import AuthSuccess

log = logging.getLogger("IronDome.TUI.Setup")


class SetupScreen(Screen):
    """First-time vault creation.

    Guides the user through choosing a security level and, where applicable,
    supplying master credentials.  On success it fires ``AuthSuccess`` so the
    app-level handler transitions to the dashboard exactly like a normal login.
    """

    DEFAULT_CSS = ""

    BINDINGS = [
        ("escape", "quit_app", "Quit"),
    ]

    def __init__(self, app_state, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state = app_state
        self._bio_available: bool = False
        self._bio_type: str = "Biometric"

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self):
        with Center():
            with Vertical(id="setup-box"):
                yield Static(
                    f"{LOGO_SMALL}  FIRST-TIME SETUP",
                    id="setup-header",
                )
                yield Static(
                    "Welcome to IronDome. Create your secure vault.",
                    id="setup-welcome",
                )

                # ── Security level ──────────────────────────────────────
                yield Static("Choose your security level:", id="setup-level-label")
                with RadioSet(id="setup-mode"):
                    yield RadioButton(
                        "Biometric Only  — quick access, no password needed",
                        id="radio-bio-only",
                        value=True,
                    )
                    yield RadioButton(
                        "Biometric + Password  — maximum security",
                        id="radio-bio-pw",
                    )
                    yield RadioButton(
                        "Password Only  — traditional login",
                        id="radio-pw-only",
                    )

                # ── Biometric notice ────────────────────────────────────
                yield Static("", id="setup-bio-notice")

                # ── Credential fields ───────────────────────────────────
                yield Input(
                    placeholder="Username (min 4 characters)",
                    id="setup-username",
                    classes="hidden",
                )
                yield Input(
                    placeholder="Master password (min 8 characters)",
                    password=True,
                    id="setup-password",
                    classes="hidden",
                )
                yield Input(
                    placeholder="Confirm master password",
                    password=True,
                    id="setup-confirm",
                    classes="hidden",
                )

                # ── Recovery key display ────────────────────────────────
                yield Static("", id="setup-recovery-box", classes="hidden")

                # ── Spinner / error / actions ───────────────────────────
                yield Center(LoadingIndicator(id="setup-spinner", classes="hidden"))
                yield Static("", id="setup-error")
                with Horizontal(id="setup-actions"):
                    yield Button(
                        "Create Vault",
                        variant="primary",
                        id="btn-create",
                    )
                    yield Button("Quit", id="btn-quit")

    # ------------------------------------------------------------------
    # Mount
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        try:
            bio = self._state.auth.biometric
            self._bio_available = bio.is_available()
            self._bio_type = bio.get_type() if self._bio_available else "Biometric"
        except Exception as exc:
            log.warning("Could not detect biometric availability: %s", exc)
            self._bio_available = False

        self._update_mode_ui()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        self._update_mode_ui()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-quit":
            self.app.exit()
        elif event.button.id == "btn-create":
            # If we are in the recovery-key display phase, "Create Vault" becomes
            # "Continue" — dismiss setup and go to the dashboard.
            recovery_box = self.query_one("#setup-recovery-box")
            if "hidden" not in recovery_box.classes:
                self._finish_to_dashboard()
            else:
                self._attempt_create()
        elif event.button.id == "btn-continue":
            self._finish_to_dashboard()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id in ("setup-username", "setup-password", "setup-confirm"):
            self._attempt_create()

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    def _selected_mode(self) -> str:
        """Return the currently selected mode identifier."""
        try:
            radio_set = self.query_one("#setup-mode", RadioSet)
            pressed = radio_set.pressed_button
            if pressed is None:
                return "password_only"
            btn_id = pressed.id
            if btn_id == "radio-bio-only":
                return "biometric_only"
            if btn_id == "radio-bio-pw":
                return "biometric_password"
            return "password_only"
        except Exception:
            return "password_only"

    def _update_mode_ui(self) -> None:
        """Show/hide fields and notices based on the current radio selection."""
        mode = self._selected_mode()
        needs_password = mode in ("biometric_password", "password_only")
        needs_bio = mode in ("biometric_only", "biometric_password")

        # Credential fields
        for widget_id in ("setup-username", "setup-password", "setup-confirm"):
            widget = self.query_one(f"#{widget_id}")
            if needs_password:
                widget.remove_class("hidden")
            else:
                widget.add_class("hidden")

        # Biometric notice
        bio_notice = self.query_one("#setup-bio-notice")
        if needs_bio:
            if self._bio_available:
                bio_notice.update(
                    f"{ICONS['shield']}  {self._bio_type} detected — "
                    "you will be prompted to verify your identity."
                )
            else:
                bio_notice.update(
                    f"{ICONS['warning']}  No biometric hardware detected. "
                    "Switch to Password Only mode."
                )
        else:
            bio_notice.update("")

        # Also relabel radio buttons to show detected type
        if self._bio_available:
            try:
                self.query_one("#radio-bio-only", RadioButton).label = (
                    f"{self._bio_type} Only  — quick access, no password needed"
                )
                self.query_one("#radio-bio-pw", RadioButton).label = (
                    f"{self._bio_type} + Password  — maximum security"
                )
            except Exception:
                pass
        else:
            # Disable biometric options when hardware is absent
            try:
                self.query_one("#radio-bio-only", RadioButton).disabled = True
                self.query_one("#radio-bio-pw", RadioButton).disabled = True
                # Force password-only selection if a biometric option was chosen
                if mode != "password_only":
                    self.query_one("#radio-pw-only", RadioButton).value = True
            except Exception:
                pass

        self._clear_error()

    def _show_error(self, msg: str) -> None:
        try:
            self.query_one("#setup-error").update(f"{ICONS['cross']}  {msg}")
        except Exception:
            pass

    def _clear_error(self) -> None:
        try:
            self.query_one("#setup-error").update("")
        except Exception:
            pass

    def _show_spinner(self, show: bool) -> None:
        try:
            spinner = self.query_one("#setup-spinner")
            if show:
                spinner.remove_class("hidden")
            else:
                spinner.add_class("hidden")
        except Exception:
            pass

    def _set_inputs_disabled(self, disabled: bool) -> None:
        for widget_id in ("setup-username", "setup-password", "setup-confirm",
                          "btn-create", "btn-quit"):
            try:
                self.query_one(f"#{widget_id}").disabled = disabled
            except Exception:
                pass
        try:
            self.query_one("#setup-mode").disabled = disabled
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_inputs(self) -> Optional[tuple[str, str, str]]:
        """Validate form fields.  Returns (mode, username, password) or None."""
        mode = self._selected_mode()

        if mode in ("biometric_password", "password_only"):
            username = self.query_one("#setup-username", Input).value.strip()
            password = self.query_one("#setup-password", Input).value
            confirm = self.query_one("#setup-confirm", Input).value

            if len(username) < 4:
                self._show_error("Username must be at least 4 characters.")
                return None
            if len(password) < 8:
                self._show_error("Password must be at least 8 characters.")
                return None
            if password != confirm:
                self._show_error("Passwords do not match.")
                return None

            return mode, username, password

        # biometric_only — no text credentials needed
        return mode, "", ""

    # ------------------------------------------------------------------
    # Vault creation worker
    # ------------------------------------------------------------------

    def _attempt_create(self) -> None:
        validated = self._validate_inputs()
        if validated is None:
            return

        mode, username, password = validated
        self._clear_error()
        self._show_spinner(True)
        self._set_inputs_disabled(True)
        self._run_create(mode, username, password)

    @work(thread=True)
    def _run_create(self, mode: str, username: str, password: str) -> None:
        """Execute vault creation in a background thread."""
        try:
            result = self._state.create_vault(mode, username, password)
            self.app.call_from_thread(self._on_create_result, result)
        except Exception as exc:
            log.error("Vault creation raised: %s", exc)
            self.app.call_from_thread(
                self._on_create_result,
                {"success": False, "error": str(exc), "recovery_key": None},
            )

    def _on_create_result(self, result: dict) -> None:
        self._show_spinner(False)

        if not result["success"]:
            self._set_inputs_disabled(False)
            self._show_error(result.get("error") or "Vault creation failed.")
            return

        recovery_key: Optional[str] = result.get("recovery_key")

        if recovery_key:
            # Show the recovery key and wait for the user to acknowledge
            self._show_recovery_key(recovery_key)
        else:
            # password_only — no recovery key; go straight to dashboard
            self._finish_to_dashboard()

    def _show_recovery_key(self, recovery_key: str) -> None:
        """Display the recovery key and swap the button label."""
        try:
            box = self.query_one("#setup-recovery-box")
            box.update(
                f"{ICONS['warning']}  SAVE YOUR RECOVERY KEY — shown only once!\n\n"
                f"   {recovery_key}\n\n"
                "If your biometric hardware fails this key is your ONLY way in.\n"
                "Store it somewhere safe, then click Continue."
            )
            box.remove_class("hidden")

            # Relabel the primary button
            btn = self.query_one("#btn-create", Button)
            btn.label = "I've Saved It — Continue"
            btn.disabled = False

            # Hide all input fields — they are no longer needed
            for wid in ("setup-username", "setup-password", "setup-confirm",
                        "setup-level-label", "setup-bio-notice"):
                try:
                    self.query_one(f"#{wid}").add_class("hidden")
                except Exception:
                    pass
            try:
                self.query_one("#setup-mode").add_class("hidden")
            except Exception:
                pass
            try:
                self.query_one("#setup-welcome").add_class("hidden")
            except Exception:
                pass
        except Exception as exc:
            log.error("Could not display recovery key: %s", exc)
            self._finish_to_dashboard()

    def _finish_to_dashboard(self) -> None:
        """Fire AuthSuccess so the app-level handler loads the dashboard."""
        username = self._state.username or "user"
        self.post_message(AuthSuccess(username))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_quit_app(self) -> None:
        self.app.exit()
