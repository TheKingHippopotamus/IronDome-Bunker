<p align="center">
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/IronDome-Bunker/main/iron%20dome%20svgs/iron_dome_dark.svg" alt="IronDome" width="280"/>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/IronDome-Bunker/main/static/irondome-readme.svg" alt="IronDome" width="500"/>
</p>

<h3 align="center">Fortified Password Vault — TUI | AES-256 | Zero-Knowledge | Biometric | Hardware-Bound</h3>

<p align="center">
  <a href="https://pypi.org/project/IronDome/"><img src="https://img.shields.io/pypi/v/IronDome?style=for-the-badge&logo=pypi&logoColor=white&color=0073b7" alt="PyPI"></a>
  <a href="https://pypi.org/project/IronDome/"><img src="https://img.shields.io/pypi/pyversions/IronDome?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/TheKingHippopotamus/IronDome-Bunker/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0-green?style=for-the-badge" alt="License GPL-3.0"></a>
  <a href="https://pypi.org/project/IronDome/"><img src="https://img.shields.io/pypi/dm/IronDome?style=for-the-badge&color=orange&label=downloads" alt="Downloads"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/macOS-Touch_ID-000000?style=for-the-badge&logo=apple&logoColor=white" alt="macOS">
  <img src="https://img.shields.io/badge/Windows-Hello-0078D4?style=for-the-badge&logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/Linux-Fingerprint-FCC624?style=for-the-badge&logo=linux&logoColor=black" alt="Linux">
  <a href="https://textual.textualize.io/"><img src="https://img.shields.io/badge/Built_With-Textual-00FF41?style=for-the-badge&logo=python&logoColor=white" alt="Textual"></a>
</p>

<p align="center">
  <a href="https://github.com/TheKingHippopotamus/IronDome-Bunker"><img src="https://img.shields.io/github/stars/TheKingHippopotamus/IronDome-Bunker?style=for-the-badge&logo=github&color=181717" alt="GitHub Stars"></a>
  <a href="https://github.com/TheKingHippopotamus/IronDome-Bunker/issues"><img src="https://img.shields.io/github/issues/TheKingHippopotamus/IronDome-Bunker?style=for-the-badge&color=red" alt="Issues"></a>
  <a href="https://github.com/TheKingHippopotamus/IronDome-Bunker/actions"><img src="https://img.shields.io/github/actions/workflow/status/TheKingHippopotamus/IronDome-Bunker/publish.yml?style=for-the-badge&label=CI&logo=githubactions&logoColor=white" alt="CI"></a>
  <a href="https://thekinghippopotamus.github.io/IronDome-Bunker/"><img src="https://img.shields.io/badge/Website-IronDome-FFD700?style=for-the-badge&logo=firefoxbrowser&logoColor=white" alt="Website"></a>
  <a href="https://thekinghippopotamus.github.io/IronDome-Bunker/docs"><img src="https://img.shields.io/badge/Docs-Field_Manual-0073b7?style=for-the-badge&logo=readthedocs&logoColor=white" alt="Docs"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#terminal-ui">Terminal UI</a> &bull;
  <a href="#features">Features</a> &bull;
  <a href="#security-architecture">Security</a> &bull;
  <a href="#keyboard-shortcuts">Keyboard</a> &bull;
  <a href="https://thekinghippopotamus.github.io/IronDome-Bunker/">Website</a>
</p>

---

<br>

> **Your bunkers. Your machine. Your rules.**
>
> IronDome encrypts everything locally with AES-256, binds keys to your hardware, and operates on a zero-knowledge model. Full terminal UI with military-grade aesthetics. Unlock with Touch ID, Windows Hello, or fingerprint. Nothing leaves your device. Ever.

<br>

## Quick Start

```bash
pip install IronDome
```

```bash
irondome
```

Two commands. You're in the TUI. On first launch, set up your vault:

```bash
irondome-cli create bunker     # First-time setup — choose security level
irondome                       # Launch the Terminal UI
```

On first launch, choose your security level:

| Mode | How It Works | Best For |
|:-----|:-------------|:---------|
| **Biometric Only** | Touch ID / Windows Hello / Fingerprint unlocks vault key from OS keychain | Speed — single factor |
| **Biometric + Password** | Biometric gate + master password derives key via PBKDF2 | Maximum security |
| **Password Only** | Master password derives all keys via PBKDF2 | Universal compatibility |

---

## Terminal UI

IronDome's primary interface is a full Terminal User Interface built with [Textual](https://textual.textualize.io/).

```bash
irondome              # Launch TUI (default)
```

**12 screens** — splash, login, dashboard, vault browser, entry detail, password generator, save form, settings, backup, status, help, confirmation dialogs.

**Keyboard-driven** — arrow keys, Enter, Esc, Tab, hotkeys for every action. Command palette with Ctrl+P.

**Military aesthetic** — dark theme, dome green accents, amber warnings, red threats. Animated splash with IronDome art.

**Security-first** — masked input, alternate screen buffer (no scrollback leaks), clipboard auto-clear, signal handlers, memory protection.

### CLI Mode

For scripts, automation, and headless environments:

```bash
irondome-cli create bunker       # First-time vault setup
irondome-cli open airspace       # Authenticate (30-min session)
irondome-cli status              # Show vault info
irondome-cli close airspace      # Lock everything
bunker create                    # Quick-create a password entry
bunker open                      # List all entries
bunker open github               # Search by name
bunker fortify                   # Create encrypted backup
bunker settings                  # Configure preferences
```

---

## Features

<table>
<tr>
<td width="50%">

### Security

| Feature | Implementation |
|:--------|:--------------|
| **Encryption** | AES-256-CBC via Fernet |
| **Key Derivation** | PBKDF2-HMAC-SHA256 × 600,000 |
| **Zero Knowledge** | Master password never stored |
| **Hardware Binding** | Keys tied to machine identity |
| **Brute Force** | Adaptive lockout per device |
| **Sessions** | 30-min auto-timeout |
| **Biometrics** | Touch ID / Hello / fprintd |
| **Two-Factor** | Biometric gate + password |
| **Recovery** | 24-word BIP-39 phrase |

</td>
<td width="50%">

### Terminal UI

| Feature | Details |
|:--------|:--------|
| **Splash Screen** | Animated IronDome art |
| **Dashboard** | Stats, quick actions, activity feed |
| **Vault Browser** | Searchable DataTable with strength meter |
| **Password Generator** | Live preview, configurable, strength scoring |
| **Click-to-Copy** | Copy password/username, auto-clears 30s |
| **Password Reveal** | Space to toggle, auto-hides in 10s |
| **Command Palette** | Ctrl+P — fuzzy search all commands |
| **Keyboard Navigation** | Arrows, Tab, Enter, Esc, hotkeys |
| **Cross-Platform** | macOS, Windows, Linux |

</td>
</tr>
</table>

---

## Keyboard Shortcuts

| Key | Action | Where |
|:----|:-------|:------|
| `Ctrl+P` | Command palette | Everywhere |
| `Ctrl+Q` | Quit | Everywhere |
| `Ctrl+L` | Lock vault | Everywhere |
| `?` | Help overlay | Everywhere |
| `Esc` | Back / cancel | Everywhere |
| `Tab` / `Shift+Tab` | Next / previous | Everywhere |
| `Up` / `Down` | Navigate | Lists, forms |
| `Left` | Go back | Vault, detail |
| `Right` / `Enter` | Open / confirm | Vault, detail |
| `Space` | Reveal password | Detail |
| `c` | Copy password | Vault, detail |
| `u` | Copy username | Vault, detail |
| `/` | Search | Vault |
| `n` | New entry | Vault |
| `r` | Regenerate | Generator |

---

## Cross-Platform

| Platform | Terminal | Biometric | Status |
|:---------|:--------|:----------|:-------|
| **macOS** | Terminal.app, iTerm2, Alacritty, WezTerm | Touch ID | Full support |
| **Windows** | Windows Terminal, PowerShell | Windows Hello | Full support |
| **Linux** | GNOME Terminal, Konsole, Alacritty, WezTerm | fprintd | Full support |
| **SSH** | Any terminal | Falls back to password | Works |

---

## Security Architecture

### Encryption Stack

| Component | Standard |
|:----------|:---------|
| **Symmetric Encryption** | AES-256-CBC (Fernet — includes HMAC) |
| **Key Derivation** | PBKDF2-HMAC-SHA256 × 600,000 (OWASP 2023) |
| **Password Hashing** | PBKDF2-HMAC-SHA256 + unique salt |
| **Random Generation** | Python `secrets` (CSPRNG) |
| **Hardware Binding** | Machine identity (machine-id / hostname / UUID) |

### TUI Security Controls

| Control | Implementation |
|:--------|:---------------|
| **Secure input** | `Input(password=True)` — masked at widget level |
| **Alternate screen** | SMCUP/RMCUP — no scrollback buffer leaks |
| **Clipboard auto-clear** | 30-second timeout, cross-platform |
| **Signal handlers** | SIGTERM/SIGINT/SIGHUP restore terminal + clear clipboard |
| **Memory protection** | `mlockall` prevents swap, `bytearray` zeroing |
| **Password auto-hide** | 10-second reveal timer |
| **Session countdown** | Live timer in status bar, auto-lock on expiry |
| **No network** | Zero HTTP, WebSocket, or network listeners |

### Threat Model

| Threat | Defense |
|:-------|:-------|
| Vault file stolen | Hardware-bound key — useless on other machines |
| Brute force | 600k PBKDF2 + adaptive lockout |
| Memory dump | Memory locking + signal handlers |
| Clipboard sniffing | Auto-clear after 30 seconds |
| Scrollback leak | Alternate screen buffer — nothing persists |
| Man-in-the-middle | No network. Zero attack surface. |

### Vault Structure

```
~/.password_manager/
├── password_manager.log           # Non-sensitive audit trail
├── settings.json                  # User preferences
├── backups/
│   └── .passwords_backup_*.enc    # Encrypted backups
└── secrets/                       # chmod 0700
    ├── .passwords.enc             # Encrypted vault (AES-256)
    ├── salt.bin                   # Key derivation salt
    ├── .master_user.enc           # Encrypted master user
    ├── .master_hash.enc           # Encrypted PBKDF2 hash
    ├── .login_attempts.dat        # Per-device lockout counter
    └── .airspace.session          # Active session (0600)
```

---

## How It Works

```
pip install IronDome → irondome

  ┌─────────────────────────────────────────────────┐
  │              CHOOSE SECURITY LEVEL               │
  └─────────────────────┬───────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
   Biometric Only  Bio + Password  Password Only
         │              │              │
   OS Keychain     Bio gate +      PBKDF2 derives
   stores key      PBKDF2 key      vault key
         │              │              │
         └──────────────┼──────────────┘
                        ▼
              ┌─────────────────┐
              │    Vault Key    │
              └────────┬────────┘
                       │
           ┌───────────┼───────────┐
           ▼                       ▼
   Machine-Specific Key    User-Specific Key
   (hardware-bound)        (user+pass+salt)
           │                       │
           ▼                       ▼
   Encrypts master         Encrypts password
   credentials             database
```

---

## Interactive Presentation

<a href="https://colab.research.google.com/github/TheKingHippopotamus/IronDome-Bunker/blob/main/demo.ipynb"><img src="https://img.shields.io/badge/Open_Full_Presentation-Google_Colab-F9AB00?style=for-the-badge&logo=googlecolab&logoColor=white" alt="Open Presentation"></a>

Test every corner of IronDome in your browser — encryption, vault operations, auth flows, stress tests.

---

## IronDome vs Cloud Password Managers

| | IronDome | Cloud Managers |
|:--|:---------|:---------------|
| **Data location** | Your machine only | Their servers |
| **Network required** | Never | Always |
| **Zero knowledge** | True — no server exists | "Trust us" |
| **Hardware binding** | Keys tied to your machine | No |
| **Interface** | Full TUI + CLI | Browser plugin |
| **Open source** | GPL-3.0 — audit everything | Rarely |
| **Cost** | Free forever | $3-5/month |
| **Biometric** | OS-native (Touch ID, Hello, fprintd) | Browser extension |
| **Attack surface** | Zero network exposure | API, servers, CDN, employees |

---

## Requirements

- **Python** 3.8 – 3.13
- **Dependencies:** `cryptography`, `keyring`, `textual`
- **Optional:** `pyobjc-framework-LocalAuthentication` (macOS Touch ID)

---

## For Developers

```bash
git clone https://github.com/TheKingHippopotamus/IronDome-Bunker.git
cd IronDome-Bunker
pip install -e .
irondome
```

<details>
<summary><strong>Project Structure</strong></summary>

```
password_manager/
├── __init__.py          # Package + version
├── cli.py               # CLI parser (irondome-cli + bunker commands)
├── manager.py           # Core IronDome class
├── auth.py              # Authentication & master credentials
├── encryption.py        # AES-256 encryption utilities
├── biometric.py         # Cross-platform biometric auth
├── keystore.py          # OS keychain integration
├── airspace.py          # Session management
├── session.py           # Timeout & lockout tracking
├── storage.py           # Encrypted file storage
├── settings.py          # User preferences
├── generator.py         # Password generation
├── utils.py             # Utility functions
├── logger.py            # Logging setup
├── constants.py         # Constants
└── tui/                 # Terminal UI (Textual)
    ├── app.py           # Main application + command palette
    ├── irondome.tcss    # Military-themed stylesheet
    ├── theme.py         # Design tokens + ASCII art
    ├── ascii_art.py     # Splash screen art
    ├── screens/         # 12 screens
    ├── widgets/         # Custom widgets
    ├── state/           # Reactive state management
    └── security/        # Clipboard, memory, signal handlers
```

</details>

### Contributing

- [CONTRIBUTING.md](CONTRIBUTING.md) — development guidelines
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — community standards
- [SECURITY.md](SECURITY.md) — vulnerability reporting

---

## License

[GNU General Public License v3.0](LICENSE) — free to use, modify, and distribute. Derivatives must remain open source.

---

<p align="center">
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/IronDome-Bunker/main/static/king-hippo.svg" alt="King Hippopotamus" width="80"/>
  <br>
  <strong>Created & maintained by <a href="https://github.com/TheKingHippopotamus">King Hippopotamus</a></strong>
  <br><br>
  <a href="https://thekinghippopotamus.github.io/IronDome-Bunker/"><img src="https://img.shields.io/badge/Website-IronDome-FFD700?style=flat-square&logo=firefoxbrowser&logoColor=white" alt="Website"></a>
  <a href="https://github.com/TheKingHippopotamus"><img src="https://img.shields.io/badge/GitHub-TheKingHippopotamus-181717?style=flat-square&logo=github" alt="GitHub"></a>
  <a href="https://pypi.org/user/king.hippo/"><img src="https://img.shields.io/badge/PyPI-king.hippo-0073b7?style=flat-square&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://x.com/LmlyhNyr"><img src="https://img.shields.io/badge/X-@LmlyhNyr-000000?style=flat-square&logo=x&logoColor=white" alt="X"></a>
  <br><br>
  <sub>No servers. No cloud. No compromise. Your bunkers. Your machine. Your rules.</sub>
</p>
