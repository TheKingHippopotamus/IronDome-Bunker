"""IronDome TUI — Main application entry point.

Launches the full Textual-based terminal interface for IronDome.
Existing CLI commands (irondome, bunker) remain untouched.
"""

from __future__ import annotations

import os
import sys
from importlib import resources as importlib_resources
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding

from password_manager import __version__
from password_manager.tui.state.app_state import AppState
from password_manager.tui.state.events import AuthSuccess, AuthFailed, SessionExpired
from password_manager.tui.security.cleanup import install_signal_handlers
from password_manager.tui.security.memory import lock_memory
from password_manager.tui.security.clipboard import force_clear as clipboard_clear


class IronDomeApp(App):
    """The IronDome TUI application."""

    TITLE = "IronDome"
    SUB_TITLE = f"Secure Vault v{__version__}"

    CSS_PATH = "irondome.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit_app", "Quit", show=True, priority=True),
        Binding("ctrl+l", "lock_vault", "Lock", show=True),
        Binding("question_mark", "show_help", "Help"),
        Binding("ctrl+p", "command_palette", "Commands"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.state = AppState()

    def on_mount(self) -> None:
        """Start with splash screen, then login."""
        from password_manager.tui.screens.splash import SplashScreen
        self.push_screen(SplashScreen())

    # ------------------------------------------------------------------
    # Message handlers
    # ------------------------------------------------------------------

    def on_splash_screen_complete(self, message: "SplashScreen.Complete") -> None:
        """Splash finished — show login."""
        self.pop_screen()  # Remove splash
        from password_manager.tui.screens.login import LoginScreen
        self.push_screen(LoginScreen(self.state))

    def on_auth_success(self, message: AuthSuccess) -> None:
        """Auth succeeded — show dashboard."""
        self.pop_screen()  # Remove login
        from password_manager.tui.screens.dashboard import DashboardScreen
        self.push_screen(DashboardScreen(self.state))
        self.notify(
            f"Welcome back, {message.username}",
            title="Airspace Open",
            timeout=3,
        )

    def on_auth_failed(self, message: AuthFailed) -> None:
        """Auth failed — notify on login screen."""
        self.notify(message.reason, severity="error", timeout=5)

    def on_session_expired(self, message: SessionExpired) -> None:
        """Session timed out — lock the app."""
        # Clear all screens back to a lock overlay
        while len(self.screen_stack) > 1:
            self.pop_screen()
        from password_manager.tui.screens.login import LoginScreen
        self.push_screen(LoginScreen(self.state))
        self.notify("Session expired. Please re-authenticate.", severity="warning", timeout=5)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_quit_app(self) -> None:
        """Clean exit."""
        self.state.logout()
        clipboard_clear()
        self.exit()

    def action_lock_vault(self) -> None:
        """Lock vault and return to login."""
        self.state.logout()
        clipboard_clear()
        # Pop all screens
        while len(self.screen_stack) > 1:
            self.pop_screen()
        from password_manager.tui.screens.login import LoginScreen
        self.push_screen(LoginScreen(self.state))
        self.notify("Vault locked.", timeout=3)

    def action_show_help(self) -> None:
        from password_manager.tui.screens.help import HelpOverlay
        self.push_screen(HelpOverlay())


def main() -> None:
    """Entry point for the irondome-tui command."""
    # Security: install signal handlers before anything else
    install_signal_handlers()

    # Security: attempt to lock memory (prevents swap)
    lock_memory()

    # Detect if running in a real terminal
    if not sys.stdout.isatty():
        print("IronDome TUI requires an interactive terminal.", file=sys.stderr)
        sys.exit(1)

    app = IronDomeApp()
    app.run()


if __name__ == "__main__":
    main()
