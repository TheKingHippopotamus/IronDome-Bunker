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

- **Zero-knowledge** — master password never stored, only salted hash
- **Local-only** — no network communication, no telemetry, no cloud sync
- **Hardware-bound** — encryption keys derived from machine-specific identifiers
- **Defense in depth** — multiple encryption layers, session management, lockout protection
- **Minimal dependencies** — only `cryptography` library to minimize attack surface

## Responsible Disclosure

We follow responsible disclosure practices. Please allow us reasonable time to address vulnerabilities before any public disclosure.
