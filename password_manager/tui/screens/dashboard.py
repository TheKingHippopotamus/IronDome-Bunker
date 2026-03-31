"""Main dashboard — stat cards, quick actions, activity feed."""

from textual.screen import Screen
from textual.widgets import Static, Button, Header, Footer
from textual.containers import Horizontal, Vertical

from password_manager.tui.theme import ICONS
from password_manager.tui.widgets.status_bar import StatusBar


class DashboardScreen(Screen):
    """Central hub after authentication. Shows vault stats and quick actions."""

    DEFAULT_CSS = """
    DashboardScreen {
        layout: vertical;
    }

    #dash-title {
        dock: top;
        height: 1;
        background: #0D1117;
        color: #00FF41;
        text-style: bold;
        padding: 0 2;
    }

    #dash-stats {
        layout: horizontal;
        height: 7;
        margin: 1 2;
    }

    .stat-card {
        width: 1fr;
        height: 100%;
        background: #111518;
        border: solid #1E2D3D;
        padding: 1 2;
        margin: 0 1;
        content-align: center middle;
    }

    .stat-value {
        color: #00FF41;
        text-style: bold;
    }

    .stat-label {
        color: #4A5568;
    }

    #dash-actions {
        layout: grid;
        grid-size: 3 2;
        grid-gutter: 1;
        margin: 1 2;
        height: auto;
    }

    .action-btn {
        width: 100%;
        height: 3;
    }

    #dash-activity {
        height: 1fr;
        background: #111518;
        border: solid #1E2D3D;
        padding: 1 2;
        margin: 1 2;
    }

    #activity-title {
        color: #94A3B8;
        text-style: bold;
        margin-bottom: 1;
    }

    #activity-feed {
        color: #4A5568;
    }
    """

    BINDINGS = [
        ("1", "open_vault", "Vault"),
        ("2", "open_search", "Search"),
        ("3", "open_generator", "Generator"),
        ("4", "open_save", "Save New"),
        ("5", "open_backup", "Backup"),
        ("6", "open_settings", "Settings"),
        ("q", "quit_to_login", "Logout"),
        ("question_mark", "show_help", "Help"),
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
            yield Button(f"[1] {ICONS['arrow_right']} Vault", id="btn-vault", classes="action-btn")
            yield Button(f"[2] {ICONS['arrow_right']} Search", id="btn-search", classes="action-btn")
            yield Button(f"[3] {ICONS['arrow_right']} Generator", id="btn-generator", classes="action-btn")
            yield Button(f"[4] {ICONS['arrow_right']} Save New", id="btn-save", classes="action-btn")
            yield Button(f"[5] {ICONS['arrow_right']} Fortify", id="btn-backup", classes="action-btn")
            yield Button(f"[6] {ICONS['arrow_right']} Settings", id="btn-settings", classes="action-btn")

        # Activity feed
        with Vertical(id="dash-activity"):
            yield Static("RECENT ACTIVITY", id="activity-title")
            yield Static("No recent activity.", id="activity-feed")

        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_stats()
        self.set_interval(1.0, self._tick_session)

    def _refresh_stats(self) -> None:
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

        # Update status bar
        status = self.query_one(StatusBar)
        status.entry_count = len(entries)
        status.airspace_open = self._state.airspace_open
        status.time_remaining = self._state.airspace_remaining

    def _tick_session(self) -> None:
        remaining = self._state.airspace_remaining
        status = self.query_one(StatusBar)
        status.time_remaining = remaining
        status.airspace_open = self._state.airspace_open

        # Update session stat
        mins = remaining // 60
        secs = remaining % 60
        self.query_one("#stat-session").update(
            f"{self._state.username}  {mins:02d}:{secs:02d}"
        )

        if remaining <= 0 and self._state.is_authenticated:
            self._state.logout()
            from password_manager.tui.state.events import SessionExpired
            self.post_message(SessionExpired())

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
        self.app.pop_screen()

    def action_show_help(self) -> None:
        from password_manager.tui.screens.help import HelpOverlay
        self.app.push_screen(HelpOverlay())
