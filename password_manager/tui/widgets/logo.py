"""IronDome ASCII logo widget."""

from textual.widgets import Static

from password_manager.tui.theme import LOGO_LARGE


class Logo(Static):
    """Renders the IronDome ASCII art logo."""

    DEFAULT_CSS = """
    Logo {
        color: #00FF41;
        text-align: center;
        width: 100%;
        height: auto;
        content-align: center middle;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(LOGO_LARGE.strip(), **kwargs)
