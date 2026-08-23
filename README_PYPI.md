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
</p>

<p align="center">
  <img src="https://img.shields.io/badge/macOS-000000?style=flat-square&logo=apple&logoColor=white" alt="macOS">
  <img src="https://img.shields.io/badge/Windows-0078D4?style=flat-square&logo=windows11&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/Linux-FCC624?style=flat-square&logo=linux&logoColor=black" alt="Linux">
  <a href="https://textual.textualize.io/"><img src="https://img.shields.io/badge/Textual-00FF41?style=flat-square&logo=python&logoColor=black" alt="Textual"></a>
</p>

---

> **Your bunkers. Your machine. Your rules.**
>
> IronDome encrypts your vault locally with AES-128-CBC (Fernet) and derives keys with PBKDF2-HMAC-SHA256 at 600,000 iterations. Full terminal UI. Unlock with Touch ID, Windows Hello, or fprintd. There is no account, no sync, and no telemetry.
>
> One caveat, stated plainly: the brute-force lockout currently identifies your machine via `socket.gethostbyname(socket.gethostname())` on each login, which can trigger a DNS lookup for your own hostname if it is not in `/etc/hosts`. No vault data is involved, and the call is being removed.

## Quick Start

```bash
pip install IronDome
irondome
```

Two commands. Full TUI launches — splash screen, biometric auth, dashboard, vault browser, password generator.

**First-time setup:**

```bash
irondome-cli create bunker
irondome
```

## Security

- **AES-128-CBC** encryption via Fernet
- **PBKDF2-HMAC-SHA256** with 600,000 iterations (OWASP 2023)
- **Master password never stored** — only a PBKDF2 digest is written to disk, and there is no server to send it to
- **Machine-scoped metadata** — the stored master-user record is wrapped with a key derived from `/etc/machine-id`; the vault itself is protected by your master password
- **Biometric gate** — an OS authentication gate (PAM / Touch ID / Windows Hello) in front of the keyring-stored vault key. It is an access gate, not key material
- **Two-factor** mode — biometric gate + master password
- **24-character recovery code** (XXXX-XXXX-XXXX-XXXX-XXXX-XXXX format)
- **Adaptive lockout** — progressive brute-force protection
- **30-minute sessions** with auto-lock

## Terminal UI

IronDome's primary interface is a full Terminal UI built with [Textual](https://textual.textualize.io/):

- **12 screens** — splash, login, dashboard, vault, detail, generator, save, settings, backup, status, help, confirm
- **Keyboard-driven** — arrows, Tab, Enter, Esc, hotkeys for every action
- **Command palette** — Ctrl+P fuzzy search across all commands
- **Themed TUI** — dark theme, dome green, amber warnings, red threats
- **Security controls** — masked input, alternate screen buffer, clipboard auto-clear (30s), signal handlers, `mlockall` swap avoidance (TUI only, best-effort)

## CLI Mode

For scripts and automation:

```bash
irondome-cli create bunker       # First-time setup
irondome-cli open airspace       # Authenticate (30-min session)
bunker create                    # Quick-create password entry
bunker open                      # List all entries
bunker open github               # Search by name
bunker fortify                   # Encrypted backup
irondome-cli close airspace      # Lock everything
```

## Cross-Platform

| Platform | Biometric | Status |
|:---------|:----------|:-------|
| **macOS** | Touch ID | Full support |
| **Windows** | Windows Hello | Full support |
| **Linux** | fprintd (fingerprint) | Full support |
| **SSH** | Password fallback | Works |

## IronDome vs Cloud Managers

| | IronDome | Cloud Managers |
|:--|:---------|:---------------|
| **Data** | Your machine only | Their servers |
| **Network** | No network I/O in the package | Always |
| **No server** | Master password never written to disk; nothing to send it to | "Trust us" |
| **Machine-scoped metadata** | Master-user record wrapped with a machine-id key | No |
| **Open source** | GPL-3.0 | Rarely |
| **Cost** | Free | $3-5/month |

## What IronDome does not do

- **AES-128.** Fernet splits its 32-byte key into a 16-byte AES key and a 16-byte HMAC key, so the block cipher runs with a 128-bit key, not a 256-bit one.
- **The biometric check is not cryptographic.** The key sits in the OS keyring under your login credentials, not under your fingerprint.
- **No hardware security module.** Machine scoping reads `/etc/machine-id` (mode `0444`, world-readable). No TPM, no Secure Enclave.
- **`nuke` cannot defeat an SSD controller.** One random-overwrite pass, `fsync`, then unlink. On SSDs, CoW filesystems, or journaled ext4 the original blocks may survive.
- **No memory zeroing of the key.** It is held as an immutable Python `bytes` inside a `Fernet` object.
- **No independent third-party audit.** The project ships its own `pytest` suite, gated in CI before publish, but no external review. Treat this as beta software.

## Links

- [Website](https://thekinghippopotamus.github.io/IronDome-Bunker/)
- [Documentation](https://thekinghippopotamus.github.io/IronDome-Bunker/docs)
- [GitHub](https://github.com/TheKingHippopotamus/IronDome-Bunker)
- [Live Demo (Colab)](https://colab.research.google.com/github/TheKingHippopotamus/IronDome-Bunker/blob/main/demo.ipynb)

## License

[GPL-3.0](https://github.com/TheKingHippopotamus/IronDome-Bunker/blob/main/LICENSE) — free to use, modify, distribute. Derivatives must remain open source.

---

<p align="center">
  <strong>Created by <a href="https://github.com/TheKingHippopotamus">King Hippopotamus</a></strong>
  <br>
  <sub>No servers. No cloud. No compromise.</sub>
</p>
