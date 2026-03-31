"""
IronDome ASCII Art — Three terminal splash interpretations.

All art is exactly 67 characters wide per line, 15-20 rows tall.
Unicode-safe: box drawing, block elements, geometric shapes only.
No emoji, no Braille. Designed for dark terminal backgrounds.

Width formula per line:
  Framed lines:   ║ + 65-char body + ║  =  67 total
  Top/bot border: ╔/╚ + 65x═ + ╗/╝   =  67 total

Usage:
    from password_manager.tui.ascii_art import SPLASH_RADAR
    from password_manager.tui.ascii_art import SPLASH_PROFILE
    from password_manager.tui.ascii_art import SPLASH_BADGE
"""


def _R(body: str) -> str:
    """Wrap body in ║…║, enforcing exactly 67 chars total."""
    return "║" + body[:65].ljust(65) + "║"


_TOP = "╔" + "═" * 65 + "╗"
_BOT = "╚" + "═" * 65 + "╝"


# ─────────────────────────────────────────────────────────────────────
# VERSION A — RADAR VIEW  (67 wide × 15 rows)
#
# Content area per line = 65 chars.
# Layout: [12 left-HUD][sp][31 radar-box][sp][20 right-HUD] = 65
# Radar box row: │ + 29-char interior + │ = 31 chars
# ─────────────────────────────────────────────────────────────────────

def _RL(lhud: str, interior: str, rhud: str) -> str:
    l = lhud[:12].ljust(12)
    m = "│" + interior[:29].ljust(29) + "│"
    r = rhud[:20].ljust(20)
    return _R(l + " " + m + " " + r)


def _RT(lhud: str, rhud: str) -> str:
    return _R(lhud[:12].ljust(12) + " ┌" + "─" * 29 + "┐ " + rhud[:20].ljust(20))


def _RB(lhud: str, rhud: str) -> str:
    return _R(lhud[:12].ljust(12) + " └" + "─" * 29 + "┘ " + rhud[:20].ljust(20))


def _RD(lhud: str, rhud: str) -> str:
    return _R(lhud[:12].ljust(12) + " " + "═" * 31 + " " + rhud[:20].ljust(20))


SPLASH_RADAR = "\n".join([
    _TOP,
    _RT(" SYS:ONLINE ", "  RANGE :  70 km  "),
    _RL(" MODE:SWEEP ", " ·  ·  ·  · ◎ ·  ·  ·  ·  · ", "  TRACK :  04     "),
    _RL(" THREATS: 04", "   ╭───────────────────╮     ", "  ALT   : 8500m   "),
    _RL(" INTERCEPT:2", " · ╭╯  · ·  · ·  · ╰╮  ·   ", "  HDG   :  247°   "),
    _RL("            ", " ╭╯  · ─────┼─────  · ╰╮ ·  ", "  SPD   : 840m/s  "),
    _RL(" ▲  THREAT  ", " │  ·─┤ ·  ◎┼◎  · ├─·  │ ·  ", "                  "),
    _RL(" ●  LOCKED  ", " ╰╮  · ─────┼─────  ·  ╭╯ · ", "  ★ IRONDOME ★    "),
    _RL(" ▲  TRACK   ", "  ╰╮  ·  · ╲╱ · ·  · ╭╯ ·  ", "  ═════════════   "),
    _RL("            ", "   ╰───────────────────╯     ", "  SECURE VAULT    "),
    _RL(" AZ: 112°   ", " ·  ·  ·  ·  ·  ·  ·  ·  ·  ", "                  "),
    _RB(" EL:  34°   ", "  DOME   :  ACTIVE  "),
    _RD(" SPD:  840  ", "  LOCK   :  CONFIRM "),
    _R(" INTERCEPT · TGT:04 · TIME-TO-KILL: T-00:08 · FIRE SOLUTION  "),
    _BOT,
])


# ─────────────────────────────────────────────────────────────────────
# VERSION B — SIDE PROFILE  (67 wide × 17 rows)
#
# Dome arc: ╭─╯ curves spanning from col ~8 to col ~55.
# Launcher: ╔══╗ vehicle with ╔════╗ radar dish at left.
# Interceptor: ║▲ vertical trail rising from launcher.
# Explosion: ✸✸✸ burst at upper right.
# City: ┌─┐ rectangular building silhouettes at ground level.
# Ground: ▄ half-block fill + █ solid fill bottom two rows.
# ─────────────────────────────────────────────────────────────────────

SPLASH_PROFILE = "\n".join([
    _TOP,
    _R("                                                ★  THREAT ▲  "),
    _R("        ╭───────────────────────────────────╮   ╲  INBOUND   "),
    _R("      ╭─╯   IRONDOME  ·  DOME: ACTIVE       ╰─╮              "),
    _R("    ╭─╯                                  ▲      ╰─╮           "),
    _R("  ╭─╯                                   ║  ✸✸✸     ╰─╮       "),
    _R(" ╭╯                                 ▲   ╳  ✸   ✸       ╰─╮   "),
    _R("─╯                                  ║    ✸✸✸   KILL        ╰─"),
    _R("                  ▲                 ●    NEUTRALIZED          "),
    _R("                  ║                                           "),
    _R("  ╔══╗           ║▲          ┌─┐  ┌──┐  ┌───┐  ┌──┐  ┌─┐   "),
    _R("  ║  ║  ╔═════╗  ║║          │█│  │██│  │███│  │██│  │█│    "),
    _R("  ║  ║  ║[◎]  ║  ║║          │█│  │██│  │███│  │██│  │█│    "),
    _R("▄▄╚══╝▄▄╚═════╝▄▄╨╨▄▄▄▄▄▄▄▄▄███▄▄████▄▄█████▄▄████▄▄███▄▄▄▄"),
    _R("████████████████████████████████████████████████████████████████"),
    _R("                      ★  IRONDOME  ·  SECURE VAULT  v2.3.0   "),
    _BOT,
])


# ─────────────────────────────────────────────────────────────────────
# VERSION C — SHIELD BADGE  (67 wide × 20 rows)
#
# Outer frame: double-column with rank stars in side gutters.
# Structure per content line:
#   ║ + gutter(3) + ║ + inner(57) + ║ + gutter(3) + ║  = 67
#    1     3         1      57       1      3         1  = 67 ✓
#
# Top/bottom border:
#   ╔ + ═(3) + ╦ + ═(57) + ╦ + ═(3) + ╗  = 67
#    1    3    1     57     1    3     1  = 67 ✓
#
# Inner 57-char area contains the shield shape.
# Shield body lines: " ║" + 53-char content + "║ " = 57 ✓
# Shield arc lines:  ╱ and ╲ drawn at appropriate positions.
# ─────────────────────────────────────────────────────────────────────

_B_TOP = "╔═══╦" + "═" * 57 + "╦═══╗"
_B_BOT = "╚═══╩" + "═" * 57 + "╩═══╝"


def _BL(gutter: str, inner: str) -> str:
    """One badge line: ║ gutter(3) ║ inner(57) ║ gutter(3) ║ = 67."""
    g = gutter[:3].ljust(3)
    b = inner[:57].ljust(57)
    return "║" + g + "║" + b + "║" + g + "║"


def _B(inner: str) -> str:
    return _BL("   ", inner)


def _BS(inner: str) -> str:
    return _BL(" ★ ", inner)


def _SB(art: str) -> str:
    """Shield body line: ' ║' + 53-char art + '║ ' = 57 chars."""
    return " ║" + art[:53].ljust(53) + "║ "


# Shield body art strings — each exactly 53 chars or padded by _SB.
# Visual structure: the ╱╲ arc forms the top of the shield,
# a rectangular ║…║ box contains the emblem and text,
# and ╲___╱ forms the shield's pointed bottom.

SPLASH_BADGE = "\n".join([
    _B_TOP,
    _BS("  · · · · · · · · · · · · · · · · · · · · · · · ·  "),
    _B("                                                         "),
    _BS(_SB("╱▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔╲   ")),
    _B(_SB("  ★  ★  ★  ★    I R O N D O M E    ★  ★  ★  ★    ")),
    _BS(_SB("  ════════════════════════════════════════════════  ")),
    _B(_SB("             ▲                    ▲                 ")),
    _B(_SB("            ╱ ╲                  ╱ ╲                ")),
    _B(_SB("           ╱   ╲────────────────╱   ╲               ")),
    _B(_SB("          ◎──────────────╳──────────────◎           ")),
    _B(_SB("           ╲   ╱────────────────╲   ╱               ")),
    _B(_SB("            ╲ ╱                  ╲ ╱                ")),
    _B(_SB("             ▼                    ▼                 ")),
    _B(_SB("  ─────────────────────────────────────────────     ")),
    _B(_SB("        SECURE VAULT   ·   v2.3.0                   ")),
    _B(_SB("  ─────────────────────────────────────────────     ")),
    _B(_SB("                   ╲___________╱                    ")),
    _B("                                                         "),
    _BS("  · · · · · · · · · · · · · · · · · · · · · · · ·  "),
    _B_BOT,
])
