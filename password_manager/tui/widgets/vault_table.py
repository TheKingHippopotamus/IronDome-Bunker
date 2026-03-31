"""Vault entries DataTable with fuzzy search support."""

from typing import Optional

from textual.reactive import reactive
from textual.widgets import DataTable


class VaultTable(DataTable):
    """DataTable specialized for vault entries with search filtering."""

    DEFAULT_CSS = """
    VaultTable {
        height: 1fr;
    }
    """

    # All entries and currently displayed (filtered) entries
    _all_entries: list[dict] = []
    filter_term: reactive[str] = reactive("")

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.add_columns("Service", "Username", "Created", "Strength")

    def load_entries(self, entries: list[dict]) -> None:
        """Load all entries into the table."""
        self._all_entries = entries
        self._apply_filter()

    def watch_filter_term(self, value: str) -> None:
        self._apply_filter()

    def _apply_filter(self) -> None:
        """Re-render table rows based on current filter term."""
        self.clear()

        term = self.filter_term.lower()
        entries = self._all_entries

        if term:
            entries = [
                e for e in entries
                if term in e.get("website", "").lower()
                or term in e.get("username", "").lower()
                or term in e.get("notes", "").lower()
            ]

        for entry in entries:
            strength = self._get_strength_label(entry.get("password", ""))
            self.add_row(
                entry.get("website", ""),
                entry.get("username", ""),
                entry.get("created_at", ""),
                strength,
                key=f"{entry.get('website', '')}:{entry.get('username', '')}",
            )

    def get_selected_entry(self) -> Optional[dict]:
        """Return the entry dict for the currently selected row."""
        if self.row_count == 0:
            return None
        try:
            row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
        except Exception:
            return None

        key_str = str(row_key)
        for entry in self._all_entries:
            entry_key = f"{entry.get('website', '')}:{entry.get('username', '')}"
            if entry_key == key_str:
                return entry
        return None

    @staticmethod
    def _get_strength_label(password: str) -> str:
        """Quick inline strength assessment for display."""
        from password_manager.generator import calculate_password_strength
        return calculate_password_strength(password)
