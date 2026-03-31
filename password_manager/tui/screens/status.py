"""Status/Dome Info screen — read-only vault and system information."""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Vertical, Horizontal

from password_manager.tui.theme import ICONS
from password_manager.tui.widgets.status_bar import StatusBar


class StatusScreen(Screen):
    """Read-only dome information display."""

    DEFAULT_CSS = """
    StatusScreen {
        layout: vertical;
    }

    #status-title {
        dock: top;
        height: 1;
        background: #0D1117;
        color: #00FF41;
        text-style: bold;
        padding: 0 2;
    }

    #status-body {
        margin: 2 4;
        height: 1fr;
    }

    .info-section {
        background: #111518;
        border: solid #1E2D3D;
        padding: 1 2;
        margin: 1 0;
    }

    .info-section-title {
        color: #00FF41;
        text-style: bold;
        margin-bottom: 1;
    }

    .info-row {
        layout: horizontal;
        height: auto;
    }

    .info-label {
        width: 24;
        color: #4A5568;
    }

    .info-value {
        width: 1fr;
        color: #E2E8F0;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, app_state, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state = app_state

    def compose(self):
        yield Header()
        yield Static(
            f"  {ICONS['dome_active']} DOME STATUS",
            id="status-title",
        )

        info = self._state.get_storage_info()

        with Vertical(id="status-body"):
            # Vault info
            with Vertical(classes="info-section"):
                yield Static("VAULT", classes="info-section-title")
                yield self._row("Data directory:", info.get("data_directory", "N/A"))
                yield self._row("Passwords file:", info.get("passwords_file", "N/A"))
                yield self._row("Entries:", str(len(self._state.get_entries())))
                if "password_file_size" in info:
                    yield self._row("Vault size:", f"{info['password_file_size']} bytes")
                    yield self._row("Last modified:", info.get("last_modified", "N/A"))

            # Security info
            with Vertical(classes="info-section"):
                yield Static("SECURITY", classes="info-section-title")
                yield self._row("Auth mode:", self._state.get_auth_mode() or "unknown")
                yield self._row("Encryption:", "AES-256-CBC (Fernet)")
                yield self._row("KDF:", "PBKDF2-HMAC-SHA256 (600k iterations)")
                yield self._row("Key binding:", "Hardware-specific")

            # Session info
            with Vertical(classes="info-section"):
                yield Static("SESSION", classes="info-section-title")
                yield self._row("Operator:", self._state.username or "N/A")
                yield self._row("Airspace:", "OPEN" if self._state.airspace_open else "CLOSED")
                if self._state.airspace_open:
                    mins = self._state.airspace_remaining // 60
                    yield self._row("Remaining:", f"{mins} minutes")
                timeout = self._state.settings.get("session_timeout", 1800) // 60
                yield self._row("Timeout:", f"{timeout} minutes")

        yield StatusBar()
        yield Footer()

    @staticmethod
    def _row(label: str, value: str) -> Horizontal:
        return Horizontal(
            Static(label, classes="info-label"),
            Static(value, classes="info-value"),
            classes="info-row",
        )

    def action_go_back(self) -> None:
        self.app.pop_screen()
