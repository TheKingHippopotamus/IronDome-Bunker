<p align="center">
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/IronDome-Bunker/main/static/irondome-readme.svg" alt="IronDome" width="500"/>
</p>

<h3 align="center">Fortified Password Vault — TUI | AES-256 | Zero-Knowledge | Biometric</h3>

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
> IronDome encrypts everything locally with AES-256, binds keys to your hardware, and operates on a zero-knowledge model. Full terminal UI. Unlock with Touch ID, Windows Hello, or fingerprint. Nothing leaves your device. Ever.

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

- **AES-256-CBC** encryption via Fernet
- **PBKDF2-HMAC-SHA256** with 600,000 iterations (OWASP 2023)
- **Zero-knowledge** — master password never stored
- **Hardware-bound** keys tied to your machine identity
- **Biometric auth** — Touch ID (macOS), Windows Hello, fprintd (Linux)
- **Two-factor** mode — biometric gate + master password
- **24-word recovery** phrase (BIP-39 format)
- **Adaptive lockout** — progressive brute-force protection
- **30-minute sessions** with auto-lock

## Terminal UI

IronDome's primary interface is a full Terminal UI built with [Textual](https://textual.textualize.io/):

- **12 screens** — splash, login, dashboard, vault, detail, generator, save, settings, backup, status, help, confirm
- **Keyboard-driven** — arrows, Tab, Enter, Esc, hotkeys for every action
- **Command palette** — Ctrl+P fuzzy search across all commands
- **Military aesthetic** — dark theme, dome green, amber warnings, red threats
- **Security controls** — masked input, alternate screen buffer, clipboard auto-clear (30s), signal handlers, memory protection

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
| **Network** | Never | Always |
| **Zero knowledge** | True — no server | "Trust us" |
| **Hardware binding** | Keys tied to machine | No |
| **Open source** | GPL-3.0 | Rarely |
| **Cost** | Free | $3-5/month |

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
