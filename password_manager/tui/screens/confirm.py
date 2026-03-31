"""Confirmation dialog — modal yes/no prompt for destructive actions."""

from textual.screen import ModalScreen
from textual.widgets import Static, Button
from textual.containers import Center, Vertical, Horizontal

from password_manager.tui.theme import ICONS


class ConfirmDialog(ModalScreen[bool]):
    """Modal confirmation dialog. Dismisses with True/False."""

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }

    #confirm-box {
        width: 50;
        height: auto;
        background: #111518;
        border: solid #1E2D3D;
        padding: 2 4;
    }

    #confirm-message {
        color: #E2E8F0;
        text-align: center;
        width: 100%;
        margin-bottom: 2;
    }

    #confirm-actions {
        layout: horizontal;
        align: center middle;
        height: auto;
    }

    #confirm-actions Button {
        margin: 0 1;
    }

    .danger-border {
        border: solid #FF2020;
    }
    """

    BINDINGS = [
        ("y", "confirm", "Yes"),
        ("n", "cancel", "No"),
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        message: str,
        action_label: str = "Confirm",
        danger: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._message = message
        self._action_label = action_label
        self._danger = danger

    def compose(self):
        with Center():
            container = Vertical(id="confirm-box")
            if self._danger:
                container.add_class("danger-border")
            with container:
                icon = ICONS["warning"] if self._danger else ICONS["shield"]
                yield Static(f"{icon}  {self._message}", id="confirm-message")
                with Horizontal(id="confirm-actions"):
                    variant = "error" if self._danger else "primary"
                    yield Button(
                        f"[y] {self._action_label}",
                        variant=variant,
                        id="btn-confirm",
                    )
                    yield Button("[n] Cancel", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
