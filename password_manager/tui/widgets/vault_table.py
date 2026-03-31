"""Vault entries DataTable with fuzzy search support."""

from typing import Optional

from textual.reactive import reactive
from textual.widgets import DataTable


class VaultTable(DataTable):
    """DataTable specialized for vault entries with search filtering."""

    DEFAULT_CSS = ""

    filter_term: reactive[str] = reactive("")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._all_entries: list = []
        self._filtered_entries: list = []

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.add_columns("Service", "Username", "Created", "Strength")
        self.focus()

    def load_entries(self, entries: list) -> None:
        """Load all entries into the table."""
        self._all_entries = list(entries)
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

        self._filtered_entries = entries

        for i, entry in enumerate(entries):
            strength = self._get_strength_label(entry.get("password", ""))
            self.add_row(
                entry.get("website", ""),
                entry.get("username", ""),
                entry.get("created_at", ""),
                strength,
            )

    def get_selected_entry(self) -> Optional[dict]:
        """Return the entry dict for the currently selected row."""
        if self.row_count == 0 or not self._filtered_entries:
            return None
        try:
            row_idx = self.cursor_coordinate.row
            if 0 <= row_idx < len(self._filtered_entries):
                return self._filtered_entries[row_idx]
        except Exception:
            pass
        return None

    @staticmethod
    def _get_strength_label(password: str) -> str:
        """Quick inline strength assessment for display."""
        from password_manager.generator import calculate_password_strength
        return calculate_password_strength(password)
