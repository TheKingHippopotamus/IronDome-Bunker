"""Main dashboard — stat cards, quick actions, activity feed."""

import os

from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static, Button, Header, Footer
from textual.containers import Horizontal, Vertical

from password_manager.tui.theme import ICONS
from password_manager.tui.widgets.status_bar import StatusBar


class DashboardScreen(Screen):
    """Central hub after authentication. Shows vault stats and quick actions."""

    DEFAULT_CSS = ""

    BINDINGS = [
        Binding("1", "open_vault", "1: Vault", show=True),
        Binding("2", "open_search", "2: Search", show=True),
        Binding("3", "open_generator", "3: Generator", show=True),
        Binding("4", "open_save", "4: New Entry", show=True),
        Binding("5", "open_backup", "5: Fortify", show=True),
        Binding("6", "open_settings", "6: Settings", show=True),
        Binding("q", "quit_to_login", "q: Logout", show=True),
        Binding("question_mark", "show_help", "?: Help", show=True),
        Binding("down", "focus_next", "Next", show=False),
        Binding("up", "focus_previous", "Prev", show=False),
    ]

    def __init__(self, app_state, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state = app_state

    def compose(self):
        yield Header()

        yield Static(
            f"  {ICONS['dome_active']} IRONDOME BUNKER",
            id="dash-title",
        )

        # Stat cards
        with Horizontal(id="dash-stats"):
            with Vertical(classes="stat-card"):
                yield Static("VAULT ENTRIES", classes="stat-label")
                yield Static("--", id="stat-entries", classes="stat-value")

            with Vertical(classes="stat-card"):
                yield Static("AIRSPACE", classes="stat-label")
                yield Static("--", id="stat-airspace", classes="stat-value")

            with Vertical(classes="stat-card"):
                yield Static("SESSION", classes="stat-label")
                yield Static("--", id="stat-session", classes="stat-value")

        # Quick actions grid
        with Vertical(id="dash-actions"):
            yield Button(f"\\[1] {ICONS['arrow_right']} Vault", id="btn-vault", classes="action-btn")
            yield Button(f"\\[2] {ICONS['arrow_right']} Search", id="btn-search", classes="action-btn")
            yield Button(f"\\[3] {ICONS['arrow_right']} Generator", id="btn-generator", classes="action-btn")
            yield Button(f"\\[4] {ICONS['arrow_right']} Save New", id="btn-save", classes="action-btn")
            yield Button(f"\\[5] {ICONS['arrow_right']} Fortify", id="btn-backup", classes="action-btn")
            yield Button(f"\\[6] {ICONS['arrow_right']} Settings", id="btn-settings", classes="action-btn")

        # Activity feed
        with Vertical(id="dash-activity"):
            yield Static("RECENT ACTIVITY", id="activity-title")
            yield Static("No recent activity.", id="activity-feed")

        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        try:
            self._refresh_stats()
        except Exception:
            pass
        self.set_interval(1.0, self._tick_session)

    def _refresh_stats(self) -> None:
        try:
            entries = self._state.get_entries()
            self.query_one("#stat-entries").update(f"{ICONS['dome_active']} {len(entries)}")

            if self._state.airspace_open:
                mins = self._state.airspace_remaining // 60
                self.query_one("#stat-airspace").update(f"{ICONS['airspace_open']} OPEN ({mins}m)")
            else:
                self.query_one("#stat-airspace").update(f"{ICONS['airspace_closed']} CLOSED")

            self.query_one("#stat-session").update(
                f"{ICONS['check']} {self._state.username or 'unknown'}"
            )

            status = self.query_one(StatusBar)
            status.entry_count = len(entries)
            status.airspace_open = self._state.airspace_open
            status.time_remaining = self._state.airspace_remaining

            self._refresh_activity_feed()
        except Exception:
            pass

    def _refresh_activity_feed(self) -> None:
        """Read the last 5 interesting lines from the log file and display them."""
        _INTERESTING = ("login", "save", "delete", "backup", "search")
        try:
            log_path = os.path.join(self._state.data_dir, "password_manager.log")
            if not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()

            # Filter: skip DEBUG lines, keep lines containing interesting keywords
            filtered = [
                ln.rstrip()
                for ln in lines
                if "DEBUG" not in ln and any(kw in ln.lower() for kw in _INTERESTING)
            ]

            recent = filtered[-5:] if len(filtered) >= 5 else filtered

            if not recent:
                return

            # Format: trim the log line to a readable timestamp + message.
            # Log format is typically:  2024-01-01 12:00:00,123 - root - INFO - message
            formatted_lines = []
            for raw in recent:
                parts = raw.split(" - ", maxsplit=3)
                if len(parts) == 4:
                    # parts[0] = timestamp, parts[3] = message
                    ts = parts[0].strip()[:19]   # "2024-01-01 12:00:00"
                    msg = parts[3].strip()
                    formatted_lines.append(f"{ts}  {msg}")
                else:
                    formatted_lines.append(raw[:120])

            feed_text = "\n".join(formatted_lines)
            self.query_one("#activity-feed").update(feed_text)
        except Exception:
            pass

    def _tick_session(self) -> None:
        try:
            remaining = self._state.airspace_remaining
            status = self.query_one(StatusBar)
            status.time_remaining = remaining
            status.airspace_open = self._state.airspace_open

            mins = remaining // 60
            secs = remaining % 60
            self.query_one("#stat-session").update(
                f"{self._state.username}  {mins:02d}:{secs:02d}"
            )

            if remaining <= 0 and self._state.is_authenticated:
                self._state.logout()
                from password_manager.tui.state.events import SessionExpired
                self.post_message(SessionExpired())
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        action_map = {
            "btn-vault": self.action_open_vault,
            "btn-search": self.action_open_search,
            "btn-generator": self.action_open_generator,
            "btn-save": self.action_open_save,
            "btn-backup": self.action_open_backup,
            "btn-settings": self.action_open_settings,
        }
        action = action_map.get(event.button.id)
        if action:
            action()

    def action_open_vault(self) -> None:
        from password_manager.tui.screens.vault import VaultScreen
        self.app.push_screen(VaultScreen(self._state))

    def action_open_search(self) -> None:
        from password_manager.tui.screens.vault import VaultScreen
        screen = VaultScreen(self._state, focus_search=True)
        self.app.push_screen(screen)

    def action_open_generator(self) -> None:
        from password_manager.tui.screens.generator import GeneratorScreen
        self.app.push_screen(GeneratorScreen(self._state))

    def action_open_save(self) -> None:
        from password_manager.tui.screens.save import SaveScreen
        self.app.push_screen(SaveScreen(self._state))

    def action_open_backup(self) -> None:
        from password_manager.tui.screens.backup import BackupScreen
        self.app.push_screen(BackupScreen(self._state))

    def action_open_settings(self) -> None:
        from password_manager.tui.screens.settings import SettingsScreen
        self.app.push_screen(SettingsScreen(self._state))

    def action_quit_to_login(self) -> None:
        self._state.logout()
        from password_manager.tui.security.clipboard import force_clear
        force_clear()
        self.app.pop_screen()
        from password_manager.tui.screens.login import LoginScreen
        self.app.push_screen(LoginScreen(self._state))

    def action_focus_next(self) -> None:
        self.focus_next()

    def action_focus_previous(self) -> None:
        self.focus_previous()

    def action_show_help(self) -> None:
        from password_manager.tui.screens.help import HelpOverlay
        self.app.push_screen(HelpOverlay())
