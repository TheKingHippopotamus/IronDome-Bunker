"""Vault screen — searchable password list with DataTable."""

from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, Static, DataTable
from textual.containers import Vertical

from password_manager.tui.theme import ICONS
from password_manager.tui.widgets.vault_table import VaultTable
from password_manager.tui.widgets.status_bar import StatusBar
from password_manager.tui.security.clipboard import copy_with_auto_clear


class VaultScreen(Screen):
    """Browsable vault with inline search, copy, and entry actions."""

    DEFAULT_CSS = ""

    BINDINGS = [
        Binding("slash", "focus_search", "/: Search", show=True),
        Binding("c", "copy_password", "c: Copy Pass", show=True),
        Binding("u", "copy_username", "u: Copy User", show=True),
        Binding("n", "new_entry", "n: New", show=True),
        Binding("ctrl+d", "delete_entry", "^D: Delete", show=True),
        Binding("escape", "go_back", "Esc: Back", show=True),
        Binding("question_mark", "show_help", "?: Help", show=True),
        Binding("down", "focus_next", show=False),
        Binding("up", "focus_previous", show=False),
    ]

    def __init__(self, app_state, focus_search: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state = app_state
        self._focus_search = focus_search

    def compose(self):
        yield Header()
        yield Static(
            f"  {ICONS['dome_active']} VAULT ENTRIES",
            id="vault-header",
        )
        yield Input(
            placeholder="/ Search entries...",
            id="vault-search-input",
        )
        with Vertical(id="vault-body"):
            yield VaultTable(id="vault-table")
        yield Static("", id="vault-count-label")
        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        try:
            table = self.query_one("#vault-table", VaultTable)
            entries = self._state.get_entries()
            table.load_entries(entries)
            self._update_count(len(entries))

            status = self.query_one(StatusBar)
            status.entry_count = len(entries)
            status.airspace_open = self._state.airspace_open
            status.time_remaining = self._state.airspace_remaining

            if entries:
                self.notify(f"Loaded {len(entries)} entries", timeout=2)
        except Exception as exc:
            self.notify(f"Failed to load vault: {exc}", severity="error", timeout=5)

        self.set_interval(1.0, self._tick)

        if self._focus_search:
            self.query_one("#vault-search-input", Input).focus()
        else:
            # Focus table so Enter/arrow keys work immediately
            try:
                self.query_one("#vault-table", VaultTable).focus()
            except Exception:
                pass

    def _tick(self) -> None:
        try:
            status = self.query_one(StatusBar)
            status.time_remaining = self._state.airspace_remaining
        except Exception:
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "vault-search-input":
            table = self.query_one("#vault-table", VaultTable)
            table.filter_term = event.value
            self._update_count(table.row_count)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Open detail view when the user presses Enter on a row."""
        table = self.query_one("#vault-table", VaultTable)
        entry = table.get_selected_entry()
        if entry:
            from password_manager.tui.screens.detail import DetailScreen
            self.app.push_screen(DetailScreen(self._state, entry))

    def _update_count(self, count: int) -> None:
        total = len(self._state.get_entries())
        if count == total:
            self.query_one("#vault-count-label").update(f"{total} entries")
        else:
            self.query_one("#vault-count-label").update(f"{count} of {total} entries")

    def action_focus_next(self) -> None:
        self.focus_next()

    def action_focus_previous(self) -> None:
        self.focus_previous()

    def action_focus_search(self) -> None:
        self.query_one("#vault-search-input", Input).focus()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_copy_password(self) -> None:
        try:
            table = self.query_one("#vault-table", VaultTable)
            entry = table.get_selected_entry()
            if not entry:
                return
            timeout = self._state.settings.get("clipboard_timeout", 30)
            if copy_with_auto_clear(entry["password"], timeout=timeout):
                self.notify(
                    f"Password copied — clears in {timeout}s",
                    title=entry["website"],
                    timeout=3,
                )
            else:
                self.notify("Clipboard unavailable", severity="error", timeout=3)
        except Exception as exc:
            self.notify(f"Copy failed: {exc}", severity="error", timeout=3)

    def action_copy_username(self) -> None:
        table = self.query_one("#vault-table", VaultTable)
        entry = table.get_selected_entry()
        if entry:
            if copy_with_auto_clear(entry["username"], timeout=0):
                self.notify(
                    "Username copied",
                    title=entry["website"],
                    timeout=3,
                )

    def action_new_entry(self) -> None:
        from password_manager.tui.screens.save import SaveScreen
        self.app.push_screen(SaveScreen(self._state))

    def action_delete_entry(self) -> None:
        table = self.query_one("#vault-table", VaultTable)
        entry = table.get_selected_entry()
        if entry:
            from password_manager.tui.screens.confirm import ConfirmDialog
            self.app.push_screen(
                ConfirmDialog(
                    f"Delete entry for {entry['username']} at {entry['website']}?",
                    action_label="Delete",
                    danger=True,
                ),
                callback=lambda confirmed: self._do_delete(entry, confirmed),
            )

    def _do_delete(self, entry: dict, confirmed: bool) -> None:
        if confirmed:
            if self._state.delete_entry(entry["username"], entry["website"]):
                self.notify(f"Deleted {entry['website']}", timeout=3)
                table = self.query_one("#vault-table", VaultTable)
                table.load_entries(self._state.get_entries())
            else:
                self.notify("Delete failed", severity="error", timeout=3)

    def action_show_help(self) -> None:
        from password_manager.tui.screens.help import HelpOverlay
        self.app.push_screen(HelpOverlay())
