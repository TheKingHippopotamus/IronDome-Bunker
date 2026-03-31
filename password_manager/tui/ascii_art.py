"""
IronDome ASCII Art — Unified terminal splash.

Combines the Side Profile scene (dome arc, launcher, missiles, interception)
with the Shield Badge frame (military border, stars, emblem structure)
into a single harmonized composition.

Every line is exactly 67 characters wide.
Outer frame: ║ ★ ║ + 57 inner chars + ║ ★ ║  OR  ║   ║ + 57 + ║   ║
Top/bottom:  ╔═══╦ + 57×═ + ╦═══╗

Usage:
    from password_manager.tui.ascii_art import SPLASH_ART
"""


def _star(inner: str) -> str:
    """Star-decorated row: ║ ★ ║ + inner(57) + ║ ★ ║ = 67 chars."""
    return "║ ★ ║" + inner[:57].ljust(57) + "║ ★ ║"


def _plain(inner: str) -> str:
    """Plain row: ║   ║ + inner(57) + ║   ║ = 67 chars."""
    return "║   ║" + inner[:57].ljust(57) + "║   ║"


_TOP = "╔═══╦" + "═" * 57 + "╦═══╗"   # 67
_BOT = "╚═══╩" + "═" * 57 + "╩═══╝"   # 67
_DOTS = " · · · · · · · · · · · · · · · · · · · · · · · · · · "
_LINE = " ═════════════════════════════════════════════════════ "
_BLANK = " " * 57

_rows = [
    _TOP,
    _star(_DOTS),
    _plain(_BLANK),

    # Dome scene — threat inbound
    _star("                                        ★  THREAT ▲  "),
    _plain("     ╭──────────────────────────────╮   ╲  INBOUND   "),
    _plain("   ╭─╯    I R O N D O M E           ╰─╮  ╲           "),
    _star(" ╭─╯       DOME : ACTIVE          ▲    ╰─╮          "),
    _plain("╭─╯                                ║ ✸✸✸   ╰─╮       "),
    _plain("╯                             ▲    ╳  ✸ ✸      ╰─    "),
    _plain("              ▲               ║     ✸✸✸  KILL        "),
    _star("              ║               ●    NEUTRALIZED       "),

    # Launcher vehicle + city skyline
    _plain("╔══╗        ║▲      ┌─┐ ┌──┐ ┌───┐ ┌──┐ ┌─┐        "),
    _plain("║◎ ║╔═════╗ ║║      │█│ │██│ │███│ │██│ │█│        "),
    _plain("╚══╝╚═════╝▄╨╨▄▄▄▄▄███▄████▄█████▄████▄███▄▄▄▄▄  "),
    _star("██████████████████████████████████████████████████   "),

    # Bottom — big IRONDOME BUNKER wordmark
    _plain(_BLANK),
    _plain(_LINE),
    _plain(" ██╗██████╗  ██████╗ ███╗  ██╗██████╗  ██████╗ ███╗  ███╗███████╗"),
    _plain(" ██║██╔══██╗██╔═══██╗████╗ ██║██╔══██╗██╔═══██╗████╗████║██╔════╝"),
    _plain(" ██║██████╔╝██║   ██║██╔██╗██║██║  ██║██║   ██║██╔████╔██║█████╗ "),
    _plain(" ██║██╔══██╗██║   ██║██║╚████║██║  ██║██║   ██║██║╚██╔╝██║██╔══╝ "),
    _plain(" ██║██║  ██║╚██████╔╝██║ ╚███║██████╔╝╚██████╔╝██║ ╚═╝ ██║█████╗"),
    _plain(" ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚══╝╚═════╝  ╚═════╝ ╚═╝    ╚═╝╚════╝"),
    _plain("     ██████╗ ██╗   ██╗███╗  ██╗██╗  ██╗███████╗██████╗          "),
    _plain("     ██╔══██╗██║   ██║████╗ ██║██║ ██╔╝██╔════╝██╔══██╗         "),
    _plain("     ██████╔╝██║   ██║██╔██╗██║█████╔╝ █████╗  ██████╔╝         "),
    _plain("     ██╔══██╗██║   ██║██║╚████║██╔═██╗ ██╔══╝  ██╔══██╗         "),
    _plain("     ██████╔╝╚██████╔╝██║ ╚███║██║  ██╗█████╗  ██║  ██║         "),
    _plain("     ╚═════╝  ╚═════╝ ╚═╝  ╚══╝╚═╝  ╚═╝╚════╝  ╚═╝  ╚═╝         "),
    _plain(_LINE),
    _star("    ★  SECURE VAULT  ·  FORTIFIED  ·  ZERO KNOWLEDGE  ★  "),
    _plain(_BLANK),
    _star(_DOTS),
    _BOT,
]

SPLASH_ART = "\n".join(_rows)

# Legacy aliases
SPLASH_RADAR = SPLASH_ART
SPLASH_PROFILE = SPLASH_ART
SPLASH_BADGE = SPLASH_ART
SPLASH_DETAILED = SPLASH_ART
SPLASH_CLEAN = SPLASH_ART
SPLASH_COMPACT = SPLASH_ART
