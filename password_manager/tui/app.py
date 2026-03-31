"""IronDome TUI — Main application entry point.

Launches the full Textual-based terminal interface for IronDome.
Existing CLI commands (irondome, bunker) remain untouched.
"""

from __future__ import annotations

import logging
import sys
import traceback

from textual.app import App
from textual.binding import Binding

from password_manager import __version__
from password_manager.tui.state.app_state import AppState
from password_manager.tui.state.events import AuthSuccess, AuthFailed, SessionExpired
from password_manager.tui.security.cleanup import install_signal_handlers
from password_manager.tui.security.memory import lock_memory
from password_manager.tui.security.clipboard import force_clear as clipboard_clear

log = logging.getLogger("IronDome.TUI")


class IronDomeApp(App):
    """The IronDome TUI application."""

    TITLE = "IronDome"
    SUB_TITLE = f"Secure Vault v{__version__}"

    CSS_PATH = "irondome.tcss"

    COMMANDS = set()  # Disable built-in command palette (maximize, theme toggle, etc.)

    BINDINGS = [
        Binding("ctrl+q", "quit_app", "^Q: Quit", show=True, priority=True),
        Binding("ctrl+l", "lock_vault", "^L: Lock", show=True),
        Binding("question_mark", "show_help", "?: Help", show=True),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.dark = True  # Force dark mode — IronDome's military theme is dark-only
        try:
            self.state = AppState()
        except Exception as exc:
            log.error("Failed to initialize AppState: %s", exc)
            raise SystemExit(f"IronDome init failed: {exc}") from exc

    def on_mount(self) -> None:
        """Start with splash screen, then login."""
        try:
            from password_manager.tui.screens.splash import SplashScreen
            self.push_screen(SplashScreen())
        except Exception as exc:
            log.error("Failed to mount splash screen: %s", exc)
            self._fallback_to_login()

    # ------------------------------------------------------------------
    # Message handlers
    # ------------------------------------------------------------------

    def on_splash_screen_complete(self, message: "SplashScreen.Complete") -> None:
        """Splash finished — show login."""
        try:
            self.pop_screen()
            from password_manager.tui.screens.login import LoginScreen
            self.push_screen(LoginScreen(self.state))
        except Exception as exc:
            log.error("Failed to transition to login: %s", exc)
            self.notify(f"Navigation error: {exc}", severity="error", timeout=5)

    def on_auth_success(self, message: AuthSuccess) -> None:
        """Auth succeeded — show dashboard."""
        try:
            self.pop_screen()
            from password_manager.tui.screens.dashboard import DashboardScreen
            self.push_screen(DashboardScreen(self.state))
            self.notify(
                f"Welcome back, {message.username}",
                title="Airspace Open",
                timeout=3,
            )
        except Exception as exc:
            log.error("Failed to load dashboard: %s", exc)
            self.notify(f"Dashboard error: {exc}", severity="error", timeout=5)

    def on_auth_failed(self, message: AuthFailed) -> None:
        """Auth failed — notify on login screen."""
        self.notify(message.reason, severity="error", timeout=5)

    def on_session_expired(self, message: SessionExpired) -> None:
        """Session timed out — lock the app."""
        try:
            self._pop_all_screens()
            from password_manager.tui.screens.login import LoginScreen
            self.push_screen(LoginScreen(self.state))
            self.notify("Session expired. Please re-authenticate.", severity="warning", timeout=5)
        except Exception as exc:
            log.error("Failed to handle session expiry: %s", exc)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_quit_app(self) -> None:
        """Clean exit."""
        try:
            self.state.logout()
        except Exception:
            pass
        try:
            clipboard_clear()
        except Exception:
            pass
        self.exit()

    def action_lock_vault(self) -> None:
        """Lock vault and return to login."""
        try:
            self.state.logout()
            clipboard_clear()
        except Exception as exc:
            log.error("Error during lock: %s", exc)

        try:
            self._pop_all_screens()
            from password_manager.tui.screens.login import LoginScreen
            self.push_screen(LoginScreen(self.state))
            self.notify("Vault locked.", timeout=3)
        except Exception as exc:
            log.error("Failed to show lock screen: %s", exc)
            self.notify(f"Lock error: {exc}", severity="error", timeout=5)

    def action_show_help(self) -> None:
        try:
            from password_manager.tui.screens.help import HelpOverlay
            self.push_screen(HelpOverlay())
        except Exception as exc:
            self.notify(f"Help unavailable: {exc}", severity="error", timeout=3)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _pop_all_screens(self) -> None:
        """Safely pop all screens back to the default."""
        while len(self.screen_stack) > 1:
            try:
                self.pop_screen()
            except Exception:
                break

    def _fallback_to_login(self) -> None:
        """Emergency fallback — go straight to login."""
        try:
            from password_manager.tui.screens.login import LoginScreen
            self.push_screen(LoginScreen(self.state))
        except Exception as exc:
            log.critical("Cannot show login screen: %s", exc)
            self.exit()


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

    try:
        app = IronDomeApp()
        app.run()
    except KeyboardInterrupt:
        clipboard_clear()
    except Exception as exc:
        clipboard_clear()
        print(f"\nIronDome TUI crashed: {exc}", file=sys.stderr)
        log.critical("Unhandled exception: %s\n%s", exc, traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
