<p align="center">
  <img src="static/irondome-logo.svg" alt="IronDome" width="500"/>
</p>

<h3 align="center">Fortified CLI Password Manager — AES-256 | Zero-Knowledge | Hardware-Bound</h3>

<p align="center">
  <a href="https://pypi.org/project/IronDome/"><img src="https://img.shields.io/pypi/v/IronDome?style=for-the-badge&logo=pypi&logoColor=white&color=0073b7" alt="PyPI"></a>
  <a href="https://pypi.org/project/IronDome/"><img src="https://img.shields.io/pypi/pyversions/IronDome?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/TheKingHippopotamus/IronDome-Bunker/blob/main/LICENSE"><img src="https://img.shields.io/github/license/TheKingHippopotamus/IronDome-Bunker?style=for-the-badge&color=green" alt="License"></a>
  <a href="https://pypi.org/project/IronDome/"><img src="https://img.shields.io/pypi/dm/IronDome?style=for-the-badge&color=orange&label=downloads" alt="Downloads"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#features">Features</a> &bull;
  <a href="#security-architecture">Security</a> &bull;
  <a href="#for-developers">Developers</a> &bull;
  <a href="#contributing">Contributing</a>
</p>

---

<br>

> **Your passwords. Your machine. Your rules.**
>
> IronDome encrypts everything locally with AES-256, binds keys to your hardware, and operates on a zero-knowledge model — your master password is never stored. Nothing leaves your device. Ever.

<br>

## Quick Start

```bash
pip install IronDome
```

```bash
bunker
```

Two commands. You're protected.

---

## Features

<table>
<tr>
<td width="50%">

### Security

- **AES-256 encryption** via Fernet
- **Zero-knowledge** — only salted PBKDF2 hash stored
- **600,000 PBKDF2 iterations** (OWASP 2023)
- **Hardware-linked keys** — data tied to your machine
- **Brute force protection** — adaptive lockouts
- **Auto-timeout** — session expires after 30min

</td>
<td width="50%">

### Management

- Generate strong, customizable passwords
- Real-time strength evaluation
- Search by domain or username
- Encrypted backup & restore
- Detailed logging (no secrets exposed)
- Intuitive CLI navigation

</td>
</tr>
</table>

---

## How It Works

```
                    ┌─────────────────────────┐
                    │     Master Password      │
                    │    (never stored)        │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │   PBKDF2-HMAC-SHA256    │
                    │   600,000 iterations    │
                    │   + unique salt         │
                    └───────────┬─────────────┘
                                │
                 ┌──────────────┼──────────────┐
                 ▼                             ▼
    ┌────────────────────┐        ┌────────────────────┐
    │  Machine-Specific  │        │   User-Specific    │
    │    System Key      │        │  Encryption Key    │
    │ (hardware-bound)   │        │ (user+pass+salt)   │
    └────────┬───────────┘        └────────┬───────────┘
             │                             │
             ▼                             ▼
    ┌────────────────────┐        ┌────────────────────┐
    │ Encrypts master    │        │ Encrypts password  │
    │ credentials        │        │ database           │
    └────────────────────┘        └────────────────────┘
```

---

## Usage

### First-Time Setup

On first run, create your master account:
1. Enter a master username (min 4 characters)
2. Create a strong master password (min 8 characters)
3. Confirm your master password

### Main Menu

```
╔══════════════════════════════╗
║     === Password Manager === ║
║     Logged in as: nir        ║
╠══════════════════════════════╣
║  1. Generate a new password  ║
║  2. Save a password          ║
║  3. Find passwords           ║
║  4. List all websites        ║
║  5. Delete a password        ║
║  6. Create backup            ║
║  7. Show storage location    ║
║  8. Logout                   ║
║  9. Exit                     ║
╚══════════════════════════════╝
```

---

## Security Architecture

### Encryption Layers

| Layer | Purpose | Scope |
|:------|:--------|:------|
| **Machine-specific system key** | Encrypts master credentials | Ties data to your hardware |
| **User-specific encryption key** | Encrypts password database | Requires both username + password |

### Authentication Security

| Feature | Implementation |
|:--------|:--------------|
| Brute force protection | Adaptive attempt limits with progressive lockout |
| Session management | Auto-timeout after 30 min inactivity |
| Sensitive operations | Require re-authentication |
| Device tracking | Per-device lockout with identifier tracking |

### Cryptographic Stack

| Component | Implementation |
|:----------|:--------------|
| Symmetric Encryption | AES-256-CBC + PKCS7 padding (Fernet) |
| Key Derivation | PBKDF2HMAC-SHA256, 600k iterations |
| Password Hashing | PBKDF2-HMAC-SHA256 + unique salt |
| Random Generation | Python `secrets` (CSPRNG) |

### Data Storage

```
~/.password_manager/
├── password_manager.log           # Non-sensitive log
├── backups/
│   └── .passwords_backup_*.enc    # Encrypted backups
└── secrets/                       # Restricted (0o700)
    ├── .passwords.enc             # Encrypted password DB
    ├── salt.bin                   # Key derivation salt
    ├── .master_user.enc           # Encrypted master user
    ├── .master_hash.enc           # Encrypted master hash
    └── .login_attempts.dat        # Lockout tracking
```

### Password Strength Scoring

```
 Excellent  ██████████████████████████████  80+
 Very Strong ████████████████████████░░░░░░  60-79
 Strong      ██████████████████░░░░░░░░░░░░  40-59
 Medium      ████████████░░░░░░░░░░░░░░░░░░  25-39
 Weak        ██████░░░░░░░░░░░░░░░░░░░░░░░░  <25
```

---

## For Developers

### Clone & Run from Source

```bash
git clone https://github.com/TheKingHippopotamus/IronDome-Bunker.git
cd IronDome-Bunker
pip install -r requirements.txt
python -m password_manager
```

### Project Structure

```
password_manager/
├── __init__.py       # Package init + version
├── __main__.py       # Entry point
├── manager.py        # Main SecurePasswordManager class
├── auth.py           # Authentication & master account
├── encryption.py     # Encryption utilities
├── session.py        # Session management & timeout
├── storage.py        # File storage operations
├── generator.py      # Password generation
├── utils.py          # Utility functions
├── logger.py         # Logging setup
└── constants.py      # Constants & configuration
```

### Contributing

We welcome contributions! Please read:

- [CONTRIBUTING.md](CONTRIBUTING.md) — development guidelines and PR process
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — community standards
- [SECURITY.md](SECURITY.md) — vulnerability reporting

---

## Requirements

- Python 3.8+
- `cryptography` library
- Windows, macOS, or Linux

---

## License

[GNU General Public License v3.0](LICENSE)

- **Attribution** — credit the original author
- **Share Source** — distribute source with binaries
- **Same License** — derivatives must use GPL-3.0
- **State Changes** — indicate modifications

---

<p align="center">
  <img src="static/king-hippo.svg" alt="King Hippopotamus" width="60"/>
  <br>
  <strong>Created & maintained by <a href="https://github.com/TheKingHippopotamus">King Hippopotamus</a></strong>
  <br>
  <sub>Built with security in mind. No data leaves your machine. Ever.</sub>
</p>
