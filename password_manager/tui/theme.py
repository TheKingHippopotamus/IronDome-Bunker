"""IronDome design tokens and theme configuration."""

# Color palette — military/cybersecurity aesthetic
COLORS = {
    "base_black": "#0A0D0F",
    "panel_surface": "#111518",
    "elevated": "#1A1F24",
    "dome_green": "#00FF41",
    "amber_alert": "#FFB300",
    "threat_red": "#FF2020",
    "intel_blue": "#00B4D8",
    "ghost_gray": "#4A5568",
    "border_dim": "#1E2D3D",
    "border_active": "#00FF41",
    "header_bg": "#0D1117",
    "text_primary": "#E2E8F0",
    "text_secondary": "#94A3B8",
}

# Status indicators (Unicode, cross-platform safe)
ICONS = {
    "dome_active": "\u25cf",     # ●
    "dome_inactive": "\u25cb",   # ○
    "airspace_open": "\u25b2",   # ▲
    "airspace_closed": "\u25bc", # ▼
    "locked": "\U0001f512",      # 🔒
    "unlocked": "\U0001f513",    # 🔓
    "shield": "\U0001f6e1",      # 🛡
    "warning": "\u26a0",         # ⚠
    "check": "\u2713",           # ✓
    "cross": "\u2717",           # ✗
    "arrow_right": "\u25b6",     # ▶
    "block_full": "\u2588",      # █
    "block_empty": "\u2591",     # ░
}

# Strength level display
STRENGTH_COLORS = {
    "Excellent": "dome_green",
    "Very Strong": "dome_green",
    "Strong": "intel_blue",
    "Medium": "amber_alert",
    "Weak": "threat_red",
}

# Spinner frames for biometric/loading
SPINNER_FRAMES = ["\u2819", "\u2839", "\u2831", "\u2838", "\u283c", "\u2834", "\u2826", "\u2827", "\u2807", "\u280f"]

# ASCII logo — compact (used in header)
LOGO_SMALL = "[ IRONDOME ]"

# Block-font wordmark
LOGO_WORDMARK = r"""
 ██╗██████╗  ██████╗ ███╗   ██╗██████╗  ██████╗ ███╗   ███╗███████╗
 ██║██╔══██╗██╔═══██╗████╗  ██║██╔══██╗██╔═══██╗████╗ ████║██╔════╝
 ██║██████╔╝██║   ██║██╔██╗ ██║██║  ██║██║   ██║██╔████╔██║█████╗
 ██║██╔══██╗██║   ██║██║╚██╗██║██║  ██║██║   ██║██║╚██╔╝██║██╔══╝
 ██║██║  ██║╚██████╔╝██║ ╚████║██████╔╝╚██████╔╝██║ ╚═╝ ██║███████╗
 ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚══════╝
"""

# High-fidelity dome ASCII art (derived from iron_dome_dark.svg)
# Elements: shield dome arc, radar dish with sweep, pulse rings,
# interceptor missile trails, explosion burst, military launcher vehicle,
# HUD targeting overlay, status readouts
LOGO_DOME = r"""
                                  ╱ ★ INTERCEPT
                                ╱
                    ░ ░ ░ ░ ░ ●══════╗          ✦ ·  ·
               ░ ░               ░ ░  ║       ✦      · ·
          ░ ░    ╭━━━━━━━━━━━━━━━━━╮  ║    ✦   ·  ·
       ░ ░      ╭┫  ◠  ◠  ◠  ◠  ◠ ┣╮ ║  ✦       ·
     ░ ░       ╭┫  ◠     ◠     ◠    ┣╮  ✦   · ·
    ░ ░       ╭┫      ┏━━━━━━━┓      ┣╮            ※ THREAT
   ░ ░       ╭┫       ┃ DOME  ┃       ┣╮          ╱ NEUTRALIZED
   ░ ░       ┃        ┃ACTIVE ┃        ┃        ✸
   ░ ░       ┃        ┗━━━━━━━┛        ┃      ╱
   ░ ░       ┃     · · · ╱╲ · · ·      ┃    ╱
   ░ ░       ┃    · · · ╱◎ ╲ · · ·     ┃   ╳ ─ ─ TARGET LOCK
   ░ ░       ┃   · · ·╱╱  ╲╲· · · ·   ┃
    ░ ░      ╰┫  ━━━╱╱━━━━━━╲╲━━━  ┣╯
     ░ ░      ╰┫  ╱╱▓▓▓▓▓▓▓▓▓▓╲╲  ┣╯
       ░ ░     ╰┫┃▓▓▓▓▓▓▓▓▓▓▓▓▓▓┃┣╯     ┌──────────────┐
         ░ ░    ┗◯━━━━━◯━━━━━◯━━┛       │ ▲ AIRSPACE   │
           ░ ░ ░ ░ ░ ░ ░ ░ ░ ░ ░         │   DEFENDED   │
              ═══════════════════          └──────────────┘
"""

# Combined logo for splash (dome + wordmark)
LOGO_LARGE = LOGO_DOME + LOGO_WORDMARK
