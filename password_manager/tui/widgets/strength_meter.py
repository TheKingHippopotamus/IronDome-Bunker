"""Visual password strength meter widget."""

from textual.reactive import reactive
from textual.widgets import Static

from password_manager.tui.theme import STRENGTH_COLORS, COLORS


class StrengthMeter(Static):
    """Displays a colored bar representing password strength."""

    DEFAULT_CSS = ""

    strength: reactive[str] = reactive("Weak")
    score: reactive[int] = reactive(0)

    def render(self) -> str:
        # Map strength to bar fill (0-10 blocks)
        strength_map = {
            "Excellent": 10,
            "Very Strong": 8,
            "Strong": 6,
            "Medium": 4,
            "Weak": 2,
        }
        filled = strength_map.get(self.strength, 2)
        empty = 10 - filled

        bar = "\u2588" * filled + "\u2591" * empty
        return f"  {bar}  {self.strength}"

    def watch_strength(self, value: str) -> None:
        # Remove old classes
        for cls in ("strength-excellent", "strength-strong", "strength-medium", "strength-weak"):
            self.remove_class(cls)

        # Apply new class based on strength
        if value in ("Excellent", "Very Strong"):
            self.add_class("strength-excellent")
        elif value == "Strong":
            self.add_class("strength-strong")
        elif value == "Medium":
            self.add_class("strength-medium")
        else:
            self.add_class("strength-weak")
