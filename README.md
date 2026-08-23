

<p align="center">
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/IronDome-Bunker/main/static/irondome-readme.svg" alt="IronDome" width="500"/>
</p>

<h3 align="center">Local-first password vault — TUI | AES-128-CBC (Fernet) | PBKDF2-HMAC-SHA256 | OS biometric gate</h3>

<p align="center">
  <a href="https://pypi.org/project/IronDome/"><img src="https://img.shields.io/pypi/v/IronDome?style=flat-square&logo=pypi&logoColor=white&color=0073b7" alt="PyPI"></a>
  <a href="https://pypi.org/project/IronDome/"><img src="https://img.shields.io/pypi/pyversions/IronDome?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://pypi.org/project/IronDome/"><img src="https://img.shields.io/pypi/dm/IronDome?style=flat-square&color=orange&label=downloads" alt="Downloads"></a>
  <a href="https://github.com/TheKingHippopotamus/IronDome-Bunker/blob/main/LICENSE"><img src="https://img.shields.io/github/license/TheKingHippopotamus/IronDome-Bunker?style=flat-square&color=green" alt="License"></a>
  <a href="https://github.com/TheKingHippopotamus/IronDome-Bunker"><img src="https://img.shields.io/github/stars/TheKingHippopotamus/IronDome-Bunker?style=flat-square&logo=github&color=181717" alt="Stars"></a>
  <a href="https://github.com/TheKingHippopotamus/IronDome-Bunker/actions"><img src="https://img.shields.io/github/actions/workflow/status/TheKingHippopotamus/IronDome-Bunker/publish.yml?style=flat-square&label=CI&logo=githubactions&logoColor=white" alt="CI"></a>
</p>
<p align="center">
  <img src="https://img.shields.io/badge/macOS-000000?style=flat-square&logo=apple&logoColor=white" alt="macOS">
  <img src="https://img.shields.io/badge/Windows-0078D4?style=flat-square&logo=windows11&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/Linux-FCC624?style=flat-square&logo=linux&logoColor=black" alt="Linux">
  <img src="https://img.shields.io/badge/Touch_ID-000000?style=flat-square&logo=apple&logoColor=white" alt="Touch ID">
  <img src="https://img.shields.io/badge/Windows_Hello-0078D4?style=flat-square&logo=windows11&logoColor=white" alt="Windows Hello">
  <img src="https://img.shields.io/badge/Fingerprint-4A5568?style=flat-square&logo=linux&logoColor=white" alt="Fingerprint">
  <a href="https://textual.textualize.io/"><img src="https://img.shields.io/badge/Textual-00FF41?style=flat-square&logo=python&logoColor=black" alt="Textual"></a>
  <a href="https://thekinghippopotamus.github.io/IronDome-Bunker/"><img src="https://img.shields.io/badge/Website-FFD700?style=flat-square&logo=firefoxbrowser&logoColor=black" alt="Website"></a>
  <a href="https://thekinghippopotamus.github.io/IronDome-Bunker/docs"><img src="https://img.shields.io/badge/Docs-0073b7?style=flat-square&logo=readthedocs&logoColor=white" alt="Docs"></a>
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
> IronDome encrypts your vault locally with AES-128-CBC (Fernet) and derives keys with PBKDF2-HMAC-SHA256 at 600,000 iterations. Full terminal UI. Unlock with Touch ID, Windows Hello, or fprintd. There is no account, no sync, and no telemetry: the package makes no network calls anywhere, verified by a test that fails the build if any module under `password_manager/` so much as imports a networking library. Nothing leaves your device.

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
| **Biometric Only** | An OS authentication gate (PAM / Touch ID / Windows Hello) runs in front of the vault key, which is stored in the OS keyring. It is an access gate, not key material — see [What IronDome does not do](#what-irondome-does-not-do) | Speed — single factor |
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

**Themed TUI** — dark theme, dome green accents, amber warnings, red threats. Animated splash with IronDome art.

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
irondome nuke                    # Self-destruct: overwrite and delete all vault data + keyring entries
bunker nuke                      # Alias — same self-destruct from bunker
```

---

## Features

<table>
<tr>
<td width="50%">

### Security

| Feature | Implementation |
|:--------|:--------------|
| **Encryption** | AES-128-CBC via Fernet |
| **Key Derivation** | PBKDF2-HMAC-SHA256 × 600,000 |
| **Master password** | Never stored — only a PBKDF2 digest is written to disk |
| **Machine-scoped metadata** | The stored master-user record is wrapped with a key derived from `/etc/machine-id`. The vault itself is protected by your master password |
| **Brute Force** | Adaptive lockout per device |
| **Sessions** | 30-min auto-timeout |
| **Biometrics** | OS authentication gate — Touch ID / Hello / fprintd |
| **Two-Factor** | Biometric gate + password |
| **Recovery** | 24-character hex recovery code |

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
| **Symmetric Encryption** | AES-128-CBC (Fernet — includes HMAC) |
| **Key Derivation** | PBKDF2-HMAC-SHA256 × 600,000 (OWASP 2023) |
| **Password Hashing** | PBKDF2-HMAC-SHA256 + unique salt |
| **Random Generation** | Python `secrets` (CSPRNG) |
| **Machine-scoped metadata** | Master-user record wrapped with a key derived from machine-id / hostname / UUID |

### TUI Security Controls

| Control | Implementation |
|:--------|:---------------|
| **Secure input** | `Input(password=True)` — masked at widget level |
| **Alternate screen** | SMCUP/RMCUP — no scrollback buffer leaks |
| **Clipboard auto-clear** | 30-second timeout, cross-platform |
| **Signal handlers** | SIGTERM/SIGINT/SIGHUP restore terminal + clear clipboard |
| **Memory protection** | `mlockall(MCL_CURRENT\|MCL_FUTURE)` keeps process memory out of swap — TUI only, best-effort, silently skipped if the OS refuses. The CLI does not call it |
| **Password auto-hide** | 10-second reveal timer |
| **Session countdown** | Live timer in status bar, auto-lock on expiry |
| **No network** | No network calls anywhere in the package — verified by test (`tests/test_no_network.py` fails if any module imports `socket`/`http`/`urllib`/`requests`, allowlist empty). No sockets opened, no ports bound. (The optional Docker web playground in `packaging/docker/` is a separate opt-in demo that does run a `textual-serve` HTTP/WebSocket server. It is not part of `pip install IronDome`.) |

### Threat Model

| Threat | Defense |
|:-------|:-------|
| Secrets folder copied | The master-user record is machine-scoped, so the folder alone does not yield it. The vault is protected by your master password — treat the password, not the machine, as the secret |
| Brute force | 600k PBKDF2 + adaptive lockout |
| Memory dump | Memory locking + signal handlers |
| Clipboard sniffing | Auto-clear after 30 seconds |
| Scrollback leak | Alternate screen buffer — nothing persists |
| Man-in-the-middle | Not applicable — the vault performs no network I/O, so there is no channel to intercept |

### Erasure limits

`nuke` clears the three OS-keyring entries first (while the salt is still readable), then overwrites each file once with random bytes, `fsync`s, and unlinks it. On SSDs with wear-levelling, on copy-on-write filesystems (btrfs/ZFS), or on journaled ext4, a single in-place overwrite does not guarantee the original blocks are destroyed — for guaranteed destruction use full-disk encryption and destroy the key, or your platform's secure-erase tool. `nuke` reports `success: False` and lists the leftovers if anything survives under the data directory.

### Vault Structure

```
~/.password_manager/
├── password_manager.log           # Non-sensitive audit trail
├── settings.json                  # User preferences
├── backups/
│   └── .passwords_backup_*.enc    # Encrypted backups
└── secrets/                       # chmod 0700
    ├── .passwords.enc             # Encrypted vault (AES-128-CBC)
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
   (machine-specific)      (user+pass+salt)
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
| **Network required** | No network calls anywhere in the package, verified by test | Always |
| **No server** | Your master password is never written to disk, and there is no service to send it to | "Trust us" |
| **Machine-scoped metadata** | Master-user record wrapped with a machine-id key | No |
| **Interface** | Full TUI + CLI | Browser plugin |
| **Open source** | GPL-3.0 — audit everything | Rarely |
| **Cost** | Free forever | $3-5/month |
| **Biometric** | OS-native gate (Touch ID, Hello, fprintd) | Browser extension |
| **Attack surface** | Local process only — no API, no server, no vendor | API, servers, CDN, employees |

---

## What IronDome does not do

- **AES-128.** Fernet splits its 32-byte key into a 16-byte AES key and a 16-byte HMAC key, so the block cipher runs with a 128-bit key — not the 256-bit key some tools advertise. That is not a weakness; it is simply a different number, and you should not have to read the source to learn which one you get.
- **The biometric check is not cryptographic.** It is an OS authentication gate (PAM / Touch ID / Windows Hello) in front of the keyring-stored vault key. The key sits in the OS keyring under your login credentials, not under your fingerprint. A process already running as you can read it without presenting a biometric. Use Biometric + Password if that is in your threat model.
- **No hardware security module.** Machine scoping is derived from `/etc/machine-id`, which is mode `0444` — world-readable, and it travels with any disk image or home-directory backup. There is no TPM and no Secure Enclave.
- **`nuke` cannot defeat an SSD controller.** One overwrite pass, then unlink. See [Erasure limits](#erasure-limits).
- **No memory zeroing of the key.** The vault key is held as an immutable Python `bytes` inside a `Fernet` object and cannot be overwritten in place.
- **No independent third-party audit.** The project ships its own test suite (`pytest`, run in CI before every publish), but nobody outside the project has reviewed the cryptography. Treat this as beta software.

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
pip install -e ".[dev]"
pytest -q
ruff check password_manager tests
irondome
```

The test suite covers the encryption round-trip and tamper detection, the KDF parameters, keyring create/unlock, on-disk file permissions, `nuke` completeness, and a static check that no module in `password_manager/` imports a network library. CI runs `pytest` and `ruff` before any PyPI publish.

### Building the website

The landing page prints exact numbers — how many tests the suite has, how many
screens the TUI has, which version is on PyPI. None of them are typed into the
page. `scripts/counts.py` collects the suite, parses the TUI package and reads
the version, then writes `website/src/data/counts.json`; the Astro page imports
that file. Regenerate it in the same pass that builds the site, and commit the
JSON with whatever change moved the numbers:

```bash
python scripts/counts.py            # rewrite website/src/data/counts.json
python scripts/counts.py --check    # exit 1 if the committed JSON is stale
cd website && npm ci && npm run build
```

`--check` is the form for CI: it fails the build when a test has been added and
the page would otherwise go out claiming the old count.

<details>
<summary><strong>Project Structure</strong></summary>

```
password_manager/
├── __init__.py          # Package + version
├── cli.py               # CLI parser (irondome-cli + bunker commands)
├── manager.py           # Core IronDome class
├── auth.py              # Authentication & master credentials
├── encryption.py        # Fernet/AES-128-CBC encryption utilities
├── biometric.py         # Cross-platform biometric auth
├── keystore.py          # OS keychain integration
├── airspace.py          # Session management
├── session.py           # Timeout & lockout tracking
├── storage.py           # Encrypted file storage
├── settings.py          # User preferences
├── generator.py         # Password generation
├── utils.py             # Utility functions
├── logger.py            # Logging setup
├── secure_io.py         # 0600 files / 0700 dirs for everything written
├── constants.py         # Constants
└── tui/                 # Terminal UI (Textual)
    ├── app.py           # Main application + command palette
    ├── irondome.tcss    # Dome-themed stylesheet
    ├── theme.py         # Design tokens + ASCII art
    ├── ascii_art.py     # Splash screen art
    ├── screens/         # 15 screens
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
