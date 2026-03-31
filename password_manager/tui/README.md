<p align="center">
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/IronDome-Bunker/main/iron%20dome%20svgs/iron_dome_dark.svg" alt="IronDome" width="300"/>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/IronDome-Bunker/main/static/irondome-readme.svg" alt="IronDome TUI" width="400"/>
</p>

<h3 align="center">Terminal User Interface — Military-Grade Vault Operations</h3>

<p align="center">
  <a href="https://pypi.org/project/IronDome/"><img src="https://img.shields.io/pypi/v/IronDome?style=for-the-badge&logo=pypi&logoColor=white&color=0073b7" alt="PyPI"></a>
  <a href="https://textual.textualize.io/"><img src="https://img.shields.io/badge/Built_With-Textual-00FF41?style=for-the-badge&logo=python&logoColor=white" alt="Textual"></a>
  <a href="https://github.com/TheKingHippopotamus/IronDome-Bunker/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0-green?style=for-the-badge" alt="License GPL-3.0"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#screens">Screens</a> &bull;
  <a href="#keyboard-shortcuts">Keyboard</a> &bull;
  <a href="#architecture">Architecture</a> &bull;
  <a href="#security">Security</a>
</p>

---

<br>

> **Full TUI for IronDome.** Splash screen, biometric login, vault browser, password generator, backup manager — all inside your terminal. No browser. No GUI framework. No network listener. Pure terminal. Maximum security.

<br>

## Quick Start

```bash
pip install IronDome[tui]
```

```bash
irondome-tui
```

That's it. The TUI launches in your terminal with the IronDome splash sequence.

**Prerequisites:** An existing IronDome vault. If you haven't set one up:

```bash
pip install IronDome
irondome create bunker
```

---

## Screens

IronDome TUI includes 12 screens, all navigable with keyboard shortcuts:

| Screen | Purpose | Key |
|:-------|:--------|:----|
| **Splash** | Boot animation, vault integrity check | Auto |
| **Login** | Biometric / password authentication | Auto |
| **Dashboard** | Stats, quick actions, activity feed | Home |
| **Vault** | Searchable password table | `1` |
| **Detail** | View entry, reveal/copy/delete | `Enter` |
| **Generator** | Live password generator with strength meter | `3` |
| **Save** | New entry form with inline generate | `4` |
| **Settings** | Toggle switches for all preferences | `6` |
| **Fortify** | Encrypted backup with progress bar | `5` |
| **Status** | Dome info — encryption, session, storage | `7` |
| **Help** | Full keyboard shortcut reference | `?` |
| **Confirm** | Modal yes/no for destructive actions | Auto |

---

## Keyboard Shortcuts

### Global

| Key | Action |
|:----|:-------|
| `?` | Help overlay |
| `Ctrl+Q` | Quit |
| `Ctrl+L` | Lock vault |
| `Esc` | Back / cancel |
| `Up` / `Down` | Navigate between elements |
| `Tab` / `Shift+Tab` | Next / previous panel |

### Dashboard

| Key | Action |
|:----|:-------|
| `1` | Open vault |
| `2` | Search |
| `3` | Password generator |
| `4` | New entry |
| `5` | Fortify (backup) |
| `6` | Settings |
| `q` | Logout |

### Vault

| Key | Action |
|:----|:-------|
| `/` | Focus search — fuzzy filter as you type |
| `Enter` | View entry detail |
| `c` | Copy password (auto-clears in 30s) |
| `u` | Copy username |
| `n` | New entry |
| `Ctrl+D` | Delete entry (with confirmation) |

### Entry Detail

| Key | Action |
|:----|:-------|
| `Space` | Reveal password (auto-hides in 10s) |
| `c` | Copy password |
| `u` | Copy username |
| `Ctrl+D` | Delete entry |

### Generator

| Key | Action |
|:----|:-------|
| `r` | Regenerate |
| `c` | Copy to clipboard |
| `s` | Save as new entry |

---

## Architecture

The TUI is a **pure additive layer**. Zero changes to IronDome's business logic.

```
password_manager/tui/
├── app.py                 # IronDomeApp — Textual application root
├── irondome.tcss          # Master stylesheet — all styling in one place
├── theme.py               # Color palette, icons, design tokens
├── screens/               # 12 screens
│   ├── splash.py          # Boot animation
│   ├── login.py           # All 3 auth modes
│   ├── dashboard.py       # Stats + quick actions
│   ├── vault.py           # Searchable DataTable
│   ├── detail.py          # Entry view with auto-hide reveal
│   ├── generator.py       # Live generator with strength meter
│   ├── save.py            # New entry form + inline generate
│   ├── settings.py        # Toggle switches
│   ├── backup.py          # Fortify with progress bar
│   ├── status.py          # Dome info
│   ├── confirm.py         # Modal confirmation
│   └── help.py            # Keyboard reference
├── widgets/               # 6 reusable components
│   ├── status_bar.py      # Live session countdown
│   ├── vault_table.py     # DataTable with fuzzy filter
│   ├── strength_meter.py  # Color-coded strength bar
│   ├── biometric_modal.py # Spinner during OS biometric dialog
│   ├── lock_overlay.py    # Full-screen lock on timeout
│   └── logo.py            # ASCII art banner
├── state/                 # Reactive state management
│   ├── app_state.py       # Bridge to business logic
│   └── events.py          # Custom messages
└── security/              # TUI-specific security
    ├── cleanup.py         # Signal handlers (SIGTERM/SIGINT/SIGHUP)
    ├── clipboard.py       # Auto-clear clipboard (30s)
    └── memory.py          # Memory zeroing + mlockall
```

### Design Pattern: MVP

```
Model (untouched)           Presenter (new)              View (new)
─────────────────           ───────────────              ──────────
SecurePasswordManager  ←→   AppState (reactive)    ←→    Screens
AuthManager                                              Widgets
SessionManager
Airspace
```

**One-way dependency.** `tui/` imports from `password_manager/`. The existing package never imports from `tui/`. The CLI commands (`irondome`, `bunker`) remain completely untouched.

---

## Security

The TUI adds **zero attack surface** to IronDome's existing security model.

| Control | Implementation |
|:--------|:---------------|
| **Secure input** | `Input(password=True)` — masked at widget level, never echoed |
| **Alternate screen** | Textual enables SMCUP/RMCUP — no scrollback buffer leaks |
| **Clipboard auto-clear** | Passwords cleared from clipboard after 30 seconds |
| **Signal handlers** | SIGTERM/SIGINT/SIGHUP restore terminal + clear clipboard |
| **Memory protection** | `mlockall` prevents swap, `bytearray` zeroing on secrets |
| **Password auto-hide** | Revealed passwords re-mask after 10 seconds |
| **Session timeout** | Live countdown in status bar, auto-lock on expiry |
| **No network** | No web server, no HTTP, no WebSocket — pure terminal |
| **Dark-only theme** | Forced dark mode, no theme toggle, no command palette |

### What the TUI does NOT do

- Does not store any secrets itself
- Does not modify encryption or auth logic
- Does not add network listeners
- Does not bypass biometric/password requirements
- Does not persist session state beyond the terminal process

---

## Cross-Platform

| Platform | Terminal | Biometric | Status |
|:---------|:--------|:----------|:-------|
| **macOS** | Terminal.app, iTerm2, Alacritty | Touch ID | Full support |
| **Windows** | Windows Terminal, PowerShell | Windows Hello | Full support |
| **Linux** | GNOME Terminal, Konsole, Alacritty | fprintd | Full support |
| **SSH** | Any terminal | N/A (falls back to password) | Works |

**Requirements:** Python 3.8+, `textual>=0.80.0`

---

## Design System

Visual DNA derived from the [IronDome dark SVG](../../iron%20dome%20svgs/iron_dome_dark.svg) — military radar, shield dome, pulse rings, interception arcs.

### Splash Art (ASCII)

```
                    ░░░░░░░░░░░░░░░░░
               ░░░░░                   ░░░░░
           ░░░░    ╭─────────────────╮    ░░░░
        ░░░       ╭╯  ◠   ◠   ◠   ◠  ╰╮       ░░░
      ░░░        ╭╯ ◠       ◠       ◠  ╰╮        ░░░
    ░░░         ╭╯     ╭─────────╮      ╰╮         ░░░
   ░░          ╭╯      │ ◉ DOME  │       ╰╮          ░░
  ░░          ╭╯       │  ACTIVE │        ╰╮          ░░
  ░░         ╭╯     ·  · ╱╲ ·  ·  ·      ╰╮         ░░
  ░░        ╭╯      · · ╱    ╲ · · ·        ╰╮        ░░
  ░░        │      · · ╱  ╱◎╲  ╲ · ·          │        ░░
  ░░        │     ────╱──╱────╲──╲────          │       ░░
   ░░       ╰╮   ┃▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓┃        ╭╯      ░░
    ░░░       ╰╮  ┗━◯━━━━━━◯━━━━━━◯━━┛       ╭╯     ░░░
      ░░░       ╰──────────────────────────╯       ░░░
         ░░░░░                           ░░░░░
              ░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

The dome represents the shield + radar from the SVG. Pulse rings (`░`) are the defense perimeter. The vehicle with wheels (`◯`) is the mobile launcher. Radar sweep dots (`·`) show active scanning.

### Color Palette

| Token | Color | Usage |
|:------|:------|:------|
| Dome Green | `#00FF41` | Active, success, unlocked |
| Amber Alert | `#FFB300` | Warning, session nearing expiry |
| Threat Red | `#FF2020` | Locked, critical, auth failed |
| Intel Blue | `#00B4D8` | Info, selected item |
| Ghost Gray | `#4A5568` | Disabled, secondary text |
| Base Black | `#0A0D0F` | Background |

All styling lives in a single file: `irondome.tcss`.

---

## Development

```bash
git clone https://github.com/TheKingHippopotamus/IronDome-Bunker.git
cd IronDome-Bunker
pip install -e ".[tui]"
irondome-tui
```

### Run with Textual dev tools

```bash
textual run --dev password_manager.tui.app:IronDomeApp
```

---

<p align="center">
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/IronDome-Bunker/main/static/king-hippo.svg" alt="King Hippopotamus" width="60"/>
  <br>
  <strong>Created & maintained by <a href="https://github.com/TheKingHippopotamus">King Hippopotamus</a></strong>
  <br>
  <sub>Your bunkers. Your machine. Your rules.</sub>
</p>
