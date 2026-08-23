# Changelog

All notable changes to IronDome are recorded here.
This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version number lives in exactly one place, `password_manager/__init__.py`;
`pyproject.toml` reads it from there via `[tool.setuptools.dynamic]`.

## [3.2.1] — 2026-08-23

A truth-in-advertising release. No new features: every change here either
corrects something the project claimed but did not do, or adds the machinery
that keeps such a gap from reopening.

### Fixed

- **`nuke` missed `.device_id` and still reported success.** `_TOP_LEVEL_FILES`
  did not include the persistent machine identifier written to
  `~/.password_manager/.device_id`, so it survived a command documented as
  erasing all data. Worse, the final step skipped its `rmdir` silently when the
  data directory was non-empty and appended no error, leaving `success: True`.
  `execute_nuke()` now enumerates the data directory and, if anything survives,
  returns `success: False` with every leftover named.
- **A DNS lookup ran on every login.** `get_machine_info()` called
  `socket.gethostbyname(socket.gethostname())` on each login and each
  failed-login accounting pass. On a host whose name is not in `/etc/hosts`
  that sends a query off the machine. The `socket` import is gone; the hostname
  now comes from `platform.node()`, which does not resolve it. The `ip_address`
  field is removed along with its two log-message consumers.
- **`tui/app.py` referenced `SplashScreen` in an annotation without importing
  it** (ruff F821). Now a `TYPE_CHECKING` import.
- **`build-binaries.yml` installed a `[binary]` extra that did not exist**, so
  PyInstaller was never installed and all four matrix legs failed. The extra is
  now defined in `pyproject.toml`.

### Changed

- **Package metadata now matches the code.** The PyPI summary said "AES-256
  encryption … zero-knowledge architecture"; Fernet splits its 32-byte key into
  a 16-byte AES key and a 16-byte HMAC key, so the cipher is AES-128-CBC. The
  description, the `aes-256` keyword and the `zero-knowledge` keyword are
  corrected or removed.
- **README.md and README_PYPI.md rewritten claim by claim.** Removed
  "zero-knowledge" (no such protocol, and no server to keep ignorant),
  "hardware binding" (it is a read of world-readable `/etc/machine-id`, and it
  wraps the master-user record, not the vault), "military-grade" framing,
  "Zero attack surface", and the absolute "Nothing leaves your device. Ever."
  The biometric feature is now described as an OS authentication gate
  (PAM / Touch ID / Windows Hello) in front of the keyring-stored vault key —
  an access gate, not key material. `mlockall` is scoped to the TUI. A new
  "What IronDome does not do" section states the limits up front, and the nuke
  section documents the SSD / copy-on-write erasure limit.
- **`publish.yml` gates on tests and lint.** A `test` job runs
  `pip install -e ".[dev]"`, `pytest -q` and `ruff check password_manager tests`;
  `publish` now `needs: test`. The gate job carries no `id-token` permission, so
  the trusted-publishing credential is minted only after the gate is green.
  Trusted publishing itself is unchanged.

### Removed

- **`zero_bytearray()`** (`tui/security/memory.py`). It had zero callers
  anywhere in the tree while the README advertised "bytearray zeroing" as a
  shipped control. Removed rather than wired up: the vault key is an immutable
  Python `bytes` inside a `Fernet` object and cannot be zeroed in place.

### Added

- **A test suite** — 143 tests in `tests/`, covering the encryption round-trip
  and tamper detection, the PBKDF2 parameters (600,000 iterations, 16-byte
  random salt, fresh IV per message), keystore create/unlock, `nuke`
  completeness in both directions, and a static proof that no module in
  `password_manager/` imports a networking library. No TTY, no biometric
  sensor, no real `HOME` and no real OS keychain are required.
- **`[dev]` and `[binary]` extras**, a `[tool.ruff.lint]` selection and
  `[tool.pytest.ini_options]`, so the lint and test commands mean the same
  thing locally and in CI.

## [3.2.0] — never published

Tagged in the repository (commit `3216a13`) but never released to PyPI: the
publish workflow did not produce a 3.2.0 artifact, so `pip install IronDome`
remained on 3.1.1 and the `nuke` command documented in the README was not
installable. Its contents ship as part of 3.2.1.

### Added

- **`irondome nuke` / `bunker nuke`** — self-destruct. Clears the three OS
  keychain entries first (while the salt is still readable), then overwrites
  each file with random bytes, `fsync`s and unlinks it, then removes the
  directory tree. See the erasure limits in the README: a single in-place
  overwrite is not a guaranteed erase on SSDs, copy-on-write filesystems or
  journaled ext4.

## [3.1.1] — 2026-04-10

Last version published to PyPI before 3.2.1.
