# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |

## Reporting a Vulnerability

**Do NOT open a public issue for security vulnerabilities.**

Instead, report vulnerabilities privately:

1. Go to the [Security Advisories](https://github.com/TheKingHippopotamus/IronDome-Bunker/security/advisories) page
2. Click "Report a vulnerability"
3. Provide a detailed description including:
   - Type of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

You will receive an acknowledgment within 48 hours. Critical vulnerabilities will be patched and released as soon as possible.

## Security Design Principles

IronDome is built on these security principles:

- **Master password never stored** — only a PBKDF2-HMAC-SHA256 digest over a random salt is written to disk, and there is no server to send the password to
- **Local-only** — no network calls anywhere in the package, enforced by `tests/test_no_network.py`; no telemetry, no cloud sync
- **Machine-scoped metadata** — the stored master-user record is wrapped with a key derived from `/etc/machine-id`. This is not hardware binding: `/etc/machine-id` is world-readable and travels with a disk image, and the vault itself is protected by the master password
- **Defense in depth** — multiple encryption layers, session management, lockout protection
- **Minimal dependencies** — `cryptography`, `keyring` and `textual` only

Known limits, stated up front: the cipher is AES-128-CBC (Fernet splits its 32-byte key into a 16-byte AES key and a 16-byte HMAC key); the biometric check is an OS authentication gate in front of the keyring-stored vault key, not key material; `nuke` overwrites once in place and cannot guarantee erasure on SSDs or copy-on-write filesystems; and the project has had no independent third-party review.

## Responsible Disclosure

We follow responsible disclosure practices. Please allow us reasonable time to address vulnerabilities before any public disclosure.
