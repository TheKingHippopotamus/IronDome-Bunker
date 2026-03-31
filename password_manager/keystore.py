#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cross-platform secure credential storage for IronDome.

Uses the OS keychain/credential store via the `keyring` library:
  - macOS  : Keychain
  - Windows : Windows Credential Manager
  - Linux  : Secret Service (GNOME Keyring / KDE Wallet)

Auth modes:
  biometric_only     — random 256-bit Fernet key stored in keychain; biometric
                       unlocks the keychain and retrieves the key directly.
  biometric_password — master password stored (encrypted) in keychain; biometric
                       retrieves it, then PBKDF2 derives the Fernet key.
  password_only      — no keychain involvement; pure PBKDF2 flow.
"""

import base64
import hashlib
import logging
import os
import secrets
import warnings
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Mirror the iteration count used everywhere else in the project
_PBKDF2_ITERATIONS = 600_000

# Human-readable recovery key format: XXXX-XXXX-XXXX-XXXX-XXXX-XXXX
_RECOVERY_KEY_GROUPS = 6
_RECOVERY_KEY_GROUP_LEN = 4
_RECOVERY_KEY_LEN = _RECOVERY_KEY_GROUPS * _RECOVERY_KEY_GROUP_LEN  # 24 hex chars

# Keyring identity constants
_SERVICE_NAME = "IronDome"
_KEY_MASTER_KEY = "master_key"
_KEY_AUTH_MODE = "auth_mode"
_KEY_RECOVERY_HASH = "recovery_hash"

# Valid auth mode values
_VALID_AUTH_MODES = {"biometric_only", "biometric_password", "password_only"}

# Try to import keyring once at module level so the import error is captured
try:
    import keyring as _keyring_lib
    _KEYRING_IMPORT_OK = True
except ImportError:
    _keyring_lib = None  # type: ignore[assignment]
    _KEYRING_IMPORT_OK = False


class SecureKeyStore:
    """
    Cross-platform secure credential storage backed by the OS keychain.

    All public methods return typed values and never raise — every failure is
    caught, optionally logged, and expressed through the return value.

    Parameters
    ----------
    salt:
        The application salt (bytes).  Used as the KDF salt for the recovery
        key hash so it is bound to this specific IronDome installation.
        When None, recovery-key operations that require a salt will fail
        gracefully.
    logger:
        An optional ``logging.Logger`` instance.  If omitted, a module-level
        logger named ``IronDome.KeyStore`` is used, which is a no-op unless
        the caller configures handlers.
    """

    SERVICE_NAME: str = _SERVICE_NAME

    def __init__(
        self,
        salt: Optional[bytes] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.salt = salt
        self.logger: logging.Logger = logger or logging.getLogger(
            "IronDome.KeyStore"
        )
        # Lazily evaluated; None means "not yet checked"
        self._keyring_available: Optional[bool] = None

    # ------------------------------------------------------------------
    # Availability
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """
        Return True if the keyring backend is usable on this system.

        The result is cached after the first call.
        """
        if self._keyring_available is not None:
            return self._keyring_available

        if not _KEYRING_IMPORT_OK:
            self.logger.warning(
                "keyring library not installed. "
                "Install it with: pip install keyring"
            )
            self._keyring_available = False
            return False

        # Probe the backend with a harmless get
        try:
            _keyring_lib.get_password(_SERVICE_NAME, "__probe__")
            self._keyring_available = True
        except Exception as exc:
            self.logger.warning(
                "keyring backend unavailable: %s. "
                "Install it with: pip install keyring",
                exc,
            )
            self._keyring_available = False

        return self._keyring_available

    # ------------------------------------------------------------------
    # Master key (biometric-only mode)
    # ------------------------------------------------------------------

    def store_master_key(self, key: bytes) -> bool:
        """
        Persist a Fernet-compatible master key in the OS keychain.

        The key is stored as a URL-safe base64 string so it survives
        round-trips through the keychain's string layer without corruption.

        Parameters
        ----------
        key:
            Raw bytes (typically 32 bytes from ``generate_fernet_key``).

        Returns
        -------
        bool
            True on success, False on any failure.
        """
        if not self.is_available():
            return False

        try:
            encoded = base64.urlsafe_b64encode(key).decode("ascii")
            _keyring_lib.set_password(_SERVICE_NAME, _KEY_MASTER_KEY, encoded)
            self.logger.info("Master key stored in OS keychain.")
            return True
        except Exception as exc:
            self.logger.error("Failed to store master key: %s", exc)
            return False

    def retrieve_master_key(self) -> Optional[bytes]:
        """
        Retrieve the master key from the OS keychain.

        Returns
        -------
        bytes or None
            The raw key bytes, or None if not found or on any error.
        """
        if not self.is_available():
            return None

        try:
            encoded = _keyring_lib.get_password(_SERVICE_NAME, _KEY_MASTER_KEY)
            if encoded is None:
                return None
            return base64.urlsafe_b64decode(encoded.encode("ascii"))
        except Exception as exc:
            self.logger.error("Failed to retrieve master key: %s", exc)
            return None

    def has_master_key(self) -> bool:
        """
        Return True if a master key is currently stored in the keychain.
        """
        if not self.is_available():
            return False

        try:
            value = _keyring_lib.get_password(_SERVICE_NAME, _KEY_MASTER_KEY)
            return value is not None
        except Exception as exc:
            self.logger.error("Failed to check master key presence: %s", exc)
            return False

    def delete_master_key(self) -> bool:
        """
        Remove the master key from the OS keychain.

        Returns
        -------
        bool
            True on success (including when the key did not exist), False on error.
        """
        if not self.is_available():
            return False

        try:
            _keyring_lib.delete_password(_SERVICE_NAME, _KEY_MASTER_KEY)
            self.logger.info("Master key deleted from OS keychain.")
            return True
        except _keyring_lib.errors.PasswordDeleteError:
            # Not present — treat as success; the desired state is achieved
            return True
        except Exception as exc:
            self.logger.error("Failed to delete master key: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Auth mode
    # ------------------------------------------------------------------

    def store_auth_mode(self, mode: str) -> bool:
        """
        Persist the auth mode string in the OS keychain.

        Parameters
        ----------
        mode:
            One of ``"biometric_only"``, ``"biometric_password"``, or
            ``"password_only"``.

        Returns
        -------
        bool
            True on success, False on any failure (including invalid mode).
        """
        if mode not in _VALID_AUTH_MODES:
            self.logger.error(
                "Invalid auth mode '%s'. Must be one of: %s",
                mode,
                ", ".join(sorted(_VALID_AUTH_MODES)),
            )
            return False

        if not self.is_available():
            return False

        try:
            _keyring_lib.set_password(_SERVICE_NAME, _KEY_AUTH_MODE, mode)
            self.logger.info("Auth mode '%s' stored in OS keychain.", mode)
            return True
        except Exception as exc:
            self.logger.error("Failed to store auth mode: %s", exc)
            return False

    def get_auth_mode(self) -> Optional[str]:
        """
        Retrieve the stored auth mode string.

        Returns
        -------
        str or None
            The mode string, or None if not set or on error.
        """
        if not self.is_available():
            return None

        try:
            value = _keyring_lib.get_password(_SERVICE_NAME, _KEY_AUTH_MODE)
            if value not in _VALID_AUTH_MODES:
                # Value is absent or corrupted — treat as unset
                return None
            return value
        except Exception as exc:
            self.logger.error("Failed to retrieve auth mode: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Fernet key generation
    # ------------------------------------------------------------------

    def generate_fernet_key(self) -> bytes:
        """
        Generate a cryptographically random Fernet-compatible key.

        Uses ``cryptography.fernet.Fernet.generate_key()`` which produces a
        32-byte URL-safe base64-encoded key suitable for direct use with
        ``Fernet(key)``.

        Returns
        -------
        bytes
            A 44-byte URL-safe base64 string (representing 32 raw bytes).
        """
        return Fernet.generate_key()

    # ------------------------------------------------------------------
    # Recovery key
    # ------------------------------------------------------------------

    def generate_recovery_key(self) -> str:
        """
        Generate a human-readable one-time recovery key.

        Format: ``XXXX-XXXX-XXXX-XXXX-XXXX-XXXX``
        (6 groups of 4 uppercase hex characters, 24 hex chars total)

        The caller is responsible for showing this to the user exactly once
        and instructing them to store it securely.  Only the hash is ever
        persisted by this module — the plaintext key is never written anywhere.

        Returns
        -------
        str
            The formatted recovery key.
        """
        raw = secrets.token_hex(_RECOVERY_KEY_LEN // 2)  # 12 bytes → 24 hex chars
        upper = raw.upper()
        groups = [
            upper[i : i + _RECOVERY_KEY_GROUP_LEN]
            for i in range(0, _RECOVERY_KEY_LEN, _RECOVERY_KEY_GROUP_LEN)
        ]
        return "-".join(groups)

    def store_recovery_hash(self, recovery_key: str) -> bool:
        """
        Derive a PBKDF2-SHA256 hash from *recovery_key* and persist it.

        The plaintext recovery key is NEVER stored.  Only the hex-encoded
        PBKDF2 digest is written to the keychain so that ``verify_recovery_key``
        can perform a constant-time comparison later.

        Parameters
        ----------
        recovery_key:
            The formatted string returned by ``generate_recovery_key``.

        Returns
        -------
        bool
            True on success, False on any failure.
        """
        if not self.is_available():
            return False

        salt = self._effective_salt()
        if salt is None:
            self.logger.error(
                "Cannot store recovery hash: no salt configured."
            )
            return False

        try:
            digest_hex = self._derive_recovery_hash(recovery_key, salt)
            _keyring_lib.set_password(
                _SERVICE_NAME, _KEY_RECOVERY_HASH, digest_hex
            )
            self.logger.info("Recovery key hash stored in OS keychain.")
            return True
        except Exception as exc:
            self.logger.error("Failed to store recovery hash: %s", exc)
            return False

    def verify_recovery_key(self, recovery_key: str) -> bool:
        """
        Verify a recovery key against the stored hash.

        The comparison is performed via a constant-time HMAC-based equality
        check (``secrets.compare_digest``) to prevent timing attacks.

        Parameters
        ----------
        recovery_key:
            The recovery key string supplied by the user.

        Returns
        -------
        bool
            True if the key is valid, False otherwise.
        """
        if not self.is_available():
            return False

        salt = self._effective_salt()
        if salt is None:
            self.logger.error(
                "Cannot verify recovery key: no salt configured."
            )
            return False

        try:
            stored_hex = _keyring_lib.get_password(
                _SERVICE_NAME, _KEY_RECOVERY_HASH
            )
            if stored_hex is None:
                self.logger.warning(
                    "No recovery hash found in keychain; verification failed."
                )
                return False

            candidate_hex = self._derive_recovery_hash(recovery_key, salt)
            return secrets.compare_digest(stored_hex, candidate_hex)
        except Exception as exc:
            self.logger.error("Failed to verify recovery key: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Clear all
    # ------------------------------------------------------------------

    def clear_all(self) -> bool:
        """
        Remove every IronDome credential stored in the OS keychain.

        This is a destructive operation intended for account reset or
        uninstallation flows.  All three keychain entries are deleted; partial
        failures are logged but the method continues to attempt each deletion.

        Returns
        -------
        bool
            True if every deletion succeeded (or was already absent), False if
            any deletion raised an unexpected error.
        """
        if not self.is_available():
            return False

        results = [
            self._delete_key(_KEY_MASTER_KEY),
            self._delete_key(_KEY_AUTH_MODE),
            self._delete_key(_KEY_RECOVERY_HASH),
        ]
        success = all(results)
        if success:
            self.logger.info(
                "All IronDome keychain entries cleared successfully."
            )
        else:
            self.logger.warning(
                "One or more IronDome keychain entries could not be cleared."
            )
        return success

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _effective_salt(self) -> Optional[bytes]:
        """
        Return the configured salt, or None if no salt was supplied.

        A salt MUST be provided in all production paths — the prior fallback of
        SHA256(service_name) was a static, globally-known value that offered no
        meaningful security for recovery-key derivation.  Callers that do not
        supply a salt will receive a logged warning and a None return so that
        dependent operations fail explicitly rather than silently weakening the
        KDF.

        In production, callers must always supply a salt obtained from
        ``PasswordStorage.load_salt()``.
        """
        if self.salt is not None:
            return self.salt

        warnings.warn(
            "SecureKeyStore: no salt provided — recovery-key operations will "
            "be rejected. Pass a salt from PasswordStorage.load_salt().",
            stacklevel=3,
        )
        self.logger.error(
            "SecureKeyStore: no salt configured; recovery-key operation "
            "cannot proceed securely."
        )
        return None

    def _derive_recovery_hash(self, recovery_key: str, salt: bytes) -> str:
        """
        Derive a hex-encoded PBKDF2-SHA256 digest from a recovery key.

        The key is normalised (stripped, upper-cased, dashes removed) before
        derivation so that minor formatting differences are tolerated.

        Parameters
        ----------
        recovery_key:
            Raw user-supplied or generated recovery key string.
        salt:
            The installation-specific salt bytes.

        Returns
        -------
        str
            Hex-encoded 32-byte PBKDF2 digest.
        """
        normalised = recovery_key.strip().upper().replace("-", "")
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=_PBKDF2_ITERATIONS,
        )
        digest = kdf.derive(normalised.encode("ascii"))
        return digest.hex()

    def _delete_key(self, username_key: str) -> bool:
        """
        Delete a single keychain entry identified by *username_key*.

        Returns True on success or when the entry was already absent.
        """
        try:
            _keyring_lib.delete_password(_SERVICE_NAME, username_key)
            return True
        except Exception:
            # Some backends raise when the entry does not exist; that is fine
            try:
                # Confirm it's actually gone rather than an access error
                still_present = _keyring_lib.get_password(
                    _SERVICE_NAME, username_key
                )
                if still_present is None:
                    return True
                self.logger.error(
                    "Failed to delete keychain entry '%s'.", username_key
                )
                return False
            except Exception as exc:
                self.logger.error(
                    "Error while verifying deletion of '%s': %s",
                    username_key,
                    exc,
                )
                return False
