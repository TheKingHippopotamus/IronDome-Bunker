"""Backup/Fortify screen — encrypted backup operations."""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, ProgressBar
from textual.containers import Vertical, Horizontal, Center
from textual import work

from password_manager.tui.theme import ICONS
from password_manager.tui.widgets.status_bar import StatusBar


class BackupScreen(Screen):
    """Backup operations with progress indicator."""

    DEFAULT_CSS = ""

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("f", "fortify", "Fortify"),
    ]

    def __init__(self, app_state, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state = app_state

    def compose(self):
        yield Header()
        yield Static(
            f"  {ICONS['shield']} FORTIFY — BACKUP OPERATIONS",
            id="backup-title",
        )

        with Vertical(id="backup-body"):
            with Vertical(id="backup-status"):
                info = self._state.get_storage_info()
                with Horizontal(classes="status-row"):
                    yield Static("Vault path:", classes="status-label")
                    yield Static(info.get("passwords_file", "N/A"), classes="status-value")

                with Horizontal(classes="status-row"):
                    yield Static("Vault size:", classes="status-label")
                    size = info.get("password_file_size", "N/A")
                    yield Static(f"{size} bytes" if isinstance(size, int) else "N/A", classes="status-value")

                with Horizontal(classes="status-row"):
                    yield Static("Last modified:", classes="status-label")
                    yield Static(info.get("last_modified", "N/A"), classes="status-value")

                with Horizontal(classes="status-row"):
                    yield Static("Entries:", classes="status-label")
                    yield Static(str(len(self._state.get_entries())), classes="status-value")

            yield Center(ProgressBar(total=100, show_eta=False, id="backup-progress"))
            yield Static("", id="backup-result")

            with Horizontal(id="backup-actions"):
                yield Button("\\[f] Fortify Now", variant="primary", id="btn-fortify")
                yield Button("Back", id="btn-back")

        yield StatusBar()
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-fortify":
            self.action_fortify()
        elif event.button.id == "btn-back":
            self.action_go_back()

    @work(thread=True)
    def action_fortify(self) -> None:
        try:
            bar = self.query_one("#backup-progress", ProgressBar)
            result_label = self.query_one("#backup-result", Static)

            self.app.call_from_thread(bar.update, progress=30)
            self.app.call_from_thread(result_label.update, "Creating encrypted backup...")

            backup_path = self._state.create_backup()

            self.app.call_from_thread(bar.update, progress=100)

            if backup_path:
                self.app.call_from_thread(
                    result_label.update,
                    f"{ICONS['check']}  Dome fortified. Backup at: {backup_path}",
                )
                self.app.call_from_thread(self.notify, "Backup created successfully", timeout=3)
            else:
                self.app.call_from_thread(
                    result_label.update,
                    f"{ICONS['cross']}  Backup failed.",
                )
                self.app.call_from_thread(self.notify, "Backup failed", severity="error", timeout=3)
        except Exception as exc:
            self.app.call_from_thread(
                self.notify, f"Backup error: {exc}", severity="error", timeout=5
            )

    def action_go_back(self) -> None:
        self.app.pop_screen()
