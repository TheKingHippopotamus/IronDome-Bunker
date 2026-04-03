"""Reactive application state — bridge between TUI and business logic.

AppState is the single source of truth. Screens read from it reactively;
mutations go through its methods, which delegate to the existing
password_manager service classes.
"""

import logging
import os
from typing import Optional

from password_manager.airspace import Airspace
from password_manager.settings import Settings
from password_manager.storage import PasswordStorage
from password_manager.session import SessionManager
from password_manager.auth import AuthManager
from password_manager.logger import setup_logger

log = logging.getLogger("IronDome.TUI.State")


class AppState:
    """Central state holder for the TUI application."""

    def __init__(self) -> None:
        self.data_dir = os.path.join(os.path.expanduser("~"), ".password_manager")

        # Core services (same as SecurePasswordManager, but without interactive auth)
        self.logger = setup_logger(os.path.join(self.data_dir, "password_manager.log"))
        self.storage = PasswordStorage(self.data_dir, self.logger)
        self.session = SessionManager(self.storage.login_attempts_file, self.logger)
        self.auth = AuthManager(self.storage, self.session, self.logger)
        self.airspace = Airspace(self.data_dir)
        self.settings = Settings(self.data_dir)

        # Cached vault entries (decrypted)
        self._vault_cache: list[dict] = []

    @property
    def is_configured(self) -> bool:
        try:
            return self.storage.master_account_exists()
        except Exception as exc:
            log.error("Failed to check vault configuration: %s", exc)
            return False

    @property
    def is_authenticated(self) -> bool:
        return self.session.session_authenticated

    @property
    def username(self) -> Optional[str]:
        return self.session.username

    @property
    def airspace_open(self) -> bool:
        try:
            return self.airspace.is_open()
        except Exception:
            return False

    @property
    def airspace_remaining(self) -> int:
        try:
            return self.airspace.remaining_seconds()
        except Exception:
            return 0

    def get_auth_mode(self) -> Optional[str]:
        try:
            salt = self.storage.load_salt()
            if not salt:
                return None
            from password_manager.keystore import SecureKeyStore
            ks = SecureKeyStore(salt=salt, logger=self.logger)
            return ks.get_auth_mode()
        except Exception as exc:
            log.error("Failed to get auth mode: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate_biometric(self) -> bool:
        """Run biometric auth flow. Blocking — call from worker thread."""
        try:
            result = self.auth.authenticate_biometric()
            if result and self.is_authenticated:
                self._refresh_vault()
                timeout = self.settings.get("session_timeout", 1800)
                auth_mode = self.get_auth_mode() or "unknown"
                self.airspace.open(timeout=timeout, auth_mode=auth_mode)
            return result
        except Exception as exc:
            log.error("Biometric auth failed: %s", exc)
            return False

    def authenticate_password(self, username: str, password: str) -> bool:
        """Authenticate with username/password. Blocking — call from worker thread."""
        salt = self.storage.load_salt()
        if not salt:
            return False

        from password_manager.encryption import hash_password, create_system_key, create_user_key
        from cryptography.fernet import Fernet
        import binascii
        import secrets as _secrets

        system_key = create_system_key(salt)
        system_fernet = Fernet(system_key)

        encrypted_username = self.storage.load_master_username()
        if not encrypted_username:
            self.session.update_login_attempts(False)
            return False

        try:
            stored_username = system_fernet.decrypt(encrypted_username).decode()
        except Exception:
            self.session.update_login_attempts(False)
            return False

        if username != stored_username:
            self.session.update_login_attempts(False)
            return False

        provided_hash = hash_password(password, salt)
        encrypted_hash = self.storage.load_password_hash()
        if not encrypted_hash:
            self.session.update_login_attempts(False)
            return False

        try:
            stored_hash = binascii.unhexlify(system_fernet.decrypt(encrypted_hash))
        except Exception:
            self.session.update_login_attempts(False)
            return False

        if _secrets.compare_digest(provided_hash, stored_hash):
            self.auth.fernet = create_user_key(username, password, salt)
            self.session.set_authenticated(username)
            self.session.update_login_attempts(True)
            self._refresh_vault()
            timeout = self.settings.get("session_timeout", 1800)
            auth_mode = self.get_auth_mode() or "unknown"
            self.airspace.open(timeout=timeout, auth_mode=auth_mode)
            return True

        self.session.update_login_attempts(False)
        return False

    def verify_password(self, password: str) -> bool:
        """Verify master password without altering session state.

        Used for re-authentication prompts on sensitive actions (e.g. delete).
        Returns True if the provided password matches the stored hash.
        """
        salt = self.storage.load_salt()
        if not salt:
            return False
        from password_manager.encryption import hash_password, create_system_key
        from cryptography.fernet import Fernet
        import binascii
        import secrets as _secrets

        try:
            system_key = create_system_key(salt)
            system_fernet = Fernet(system_key)
            encrypted_hash = self.storage.load_password_hash()
            if not encrypted_hash:
                return False
            stored_hash = binascii.unhexlify(system_fernet.decrypt(encrypted_hash))
            provided_hash = hash_password(password, salt)
            return _secrets.compare_digest(provided_hash, stored_hash)
        except Exception as exc:
            log.error("Password verification failed: %s", exc)
            return False

    def logout(self) -> None:
        try:
            self.session.logout()
            self.airspace.close()
        except Exception as exc:
            log.error("Error during logout: %s", exc)
        self._vault_cache.clear()
        self.auth.fernet = None

    # ------------------------------------------------------------------
    # Vault operations
    # ------------------------------------------------------------------

    def _refresh_vault(self) -> None:
        try:
            if self.auth.fernet:
                self._vault_cache = self.storage.load_passwords(self.auth.fernet)
        except Exception as exc:
            log.error("Failed to refresh vault: %s", exc)
            self._vault_cache = []

    def get_entries(self) -> list:
        try:
            if not self._vault_cache and self.auth.fernet:
                self._refresh_vault()
            return list(self._vault_cache)
        except Exception as exc:
            log.error("Failed to get entries: %s", exc)
            return []

    def search_entries(self, term: str) -> list[dict]:
        if len(term) < 2:
            return self.get_entries()
        term_lower = term.lower()
        return [
            e for e in self.get_entries()
            if term_lower in e.get("website", "").lower()
            or term_lower in e.get("username", "").lower()
            or term_lower in e.get("notes", "").lower()
        ]

    def save_entry(self, username: str, website: str, password: str, notes: str = "") -> bool:
        import time
        try:
            if not self.auth.fernet:
                return False
            entries = self.get_entries()
            entry = {
                "username": username,
                "website": website,
                "password": password,
                "notes": notes,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            entries = [e for e in entries if not (e["username"] == username and e["website"] == website)]
            entries.append(entry)
            if self.storage.save_passwords(entries, self.auth.fernet):
                self._vault_cache = entries
                self.logger.info(f"Saved entry for {username} at {website}")
                return True
            return False
        except Exception as exc:
            log.error("Failed to save entry: %s", exc)
            return False

    def update_entry(
        self,
        orig_username: str,
        orig_website: str,
        new_username: str,
        new_website: str,
        new_password: str,
        new_notes: str = "",
    ) -> Optional[dict]:
        """Update an existing entry. Returns the updated entry dict or None on failure."""
        import time
        try:
            if not self.auth.fernet:
                return None
            entries = self.get_entries()
            # Remove the original entry
            remaining = [
                e for e in entries
                if not (e["username"] == orig_username and e["website"] == orig_website)
            ]
            # Build the updated entry, preserving created_at from the original
            created_at = None
            for e in entries:
                if e["username"] == orig_username and e["website"] == orig_website:
                    created_at = e.get("created_at")
                    break

            updated = {
                "username": new_username,
                "website": new_website,
                "password": new_password,
                "notes": new_notes,
                "created_at": created_at or time.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            remaining.append(updated)
            if self.storage.save_passwords(remaining, self.auth.fernet):
                self._vault_cache = remaining
                self.logger.info(f"Updated entry for {new_username} at {new_website}")
                return updated
            return None
        except Exception as exc:
            log.error("Failed to update entry: %s", exc)
            return None

    def delete_entry(self, username: str, website: str) -> bool:
        try:
            if not self.auth.fernet:
                return False
            entries = self.get_entries()
            new_entries = [e for e in entries if not (e["username"] == username and e["website"] == website)]
            if len(new_entries) < len(entries):
                if self.storage.save_passwords(new_entries, self.auth.fernet):
                    self._vault_cache = new_entries
                    self.logger.info(f"Deleted entry for {username} at {website}")
                    return True
            return False
        except Exception as exc:
            log.error("Failed to delete entry: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Vault creation (first-time setup)
    # ------------------------------------------------------------------

    def create_vault(
        self,
        mode: str,
        username: str = "",
        password: str = "",
    ) -> dict:
        """Create a new vault without interactive prompts.

        Replicates the logic of ``AuthManager.setup_security_mode()`` and its
        helpers, but uses caller-supplied values instead of ``input()`` /
        ``getpass()``.  Safe to call from a worker thread.

        Parameters
        ----------
        mode:
            One of ``"biometric_only"``, ``"biometric_password"``, or
            ``"password_only"``.
        username:
            Master username (required for password modes, min 4 chars).
        password:
            Master password (required for password modes, min 8 chars).

        Returns
        -------
        dict with keys:
            ``success`` (bool)
            ``error`` (str | None) — human-readable failure reason
            ``recovery_key`` (str | None) — present for biometric modes only
        """
        import binascii
        from cryptography.fernet import Fernet
        from password_manager.encryption import (
            generate_salt,
            hash_password,
            create_system_key,
            create_user_key,
        )
        from password_manager.keystore import SecureKeyStore

        def _fail(msg: str) -> dict:
            log.error("create_vault failed: %s", msg)
            return {"success": False, "error": msg, "recovery_key": None}

        if mode not in ("biometric_only", "biometric_password", "password_only"):
            return _fail(f"Unknown mode: {mode!r}")

        # ── password modes require valid credentials ─────────────────────
        if mode in ("biometric_password", "password_only"):
            if len(username) < 4:
                return _fail("Username must be at least 4 characters.")
            if len(password) < 8:
                return _fail("Password must be at least 8 characters.")

        # ── biometric_only ───────────────────────────────────────────────
        if mode == "biometric_only":
            bio = self.auth.biometric
            if not bio.is_available():
                return _fail("Biometric hardware not available on this device.")

            if not bio.authenticate("IronDome setup — verify identity"):
                return _fail("Biometric verification failed.")

            salt = generate_salt()
            if not self.storage.save_salt(salt):
                return _fail("Could not save salt file.")

            ks = SecureKeyStore(salt=salt, logger=self.logger)
            self.auth.keystore = ks

            master_key = ks.generate_fernet_key()
            if not ks.store_master_key(master_key):
                return _fail("Could not store key in system keychain.")

            ks.store_auth_mode("biometric_only")

            recovery_key = ks.generate_recovery_key()
            ks.store_recovery_hash(recovery_key)

            # Store a placeholder account entry so master_account_exists() returns True
            system_key = create_system_key(salt)
            system_fernet = Fernet(system_key)

            bio_type = bio.get_type()
            _bio_username = f"bio_{bio_type.lower().replace(' ', '_')}"
            encrypted_username = system_fernet.encrypt(_bio_username.encode())
            self.storage.save_master_username(encrypted_username)

            placeholder_hash = hash_password("biometric_only_placeholder", salt)
            encrypted_hash = system_fernet.encrypt(binascii.hexlify(placeholder_hash))
            self.storage.save_password_hash(encrypted_hash)

            self.auth.fernet = Fernet(master_key)
            self.session.set_authenticated(_bio_username)

            return {"success": True, "error": None, "recovery_key": recovery_key}

        # ── biometric_password ───────────────────────────────────────────
        if mode == "biometric_password":
            bio = self.auth.biometric
            if not bio.is_available():
                return _fail("Biometric hardware not available on this device.")

            if not bio.authenticate("IronDome setup — verify identity"):
                return _fail("Biometric verification failed.")

            salt = generate_salt()
            if not self.storage.save_salt(salt):
                return _fail("Could not save salt file.")

            system_key = create_system_key(salt)
            system_fernet = Fernet(system_key)

            encrypted_username = system_fernet.encrypt(username.encode())
            if not self.storage.save_master_username(encrypted_username):
                return _fail("Could not save username file.")

            password_hash = hash_password(password, salt)
            encrypted_hash = system_fernet.encrypt(binascii.hexlify(password_hash))
            if not self.storage.save_password_hash(encrypted_hash):
                return _fail("Could not save password hash file.")

            self.auth.fernet = create_user_key(username, password, salt)
            self.session.set_authenticated(username)

            ks = SecureKeyStore(salt=salt, logger=self.logger)
            self.auth.keystore = ks
            ks.store_auth_mode("biometric_password")

            recovery_key = ks.generate_recovery_key()
            ks.store_recovery_hash(recovery_key)

            return {"success": True, "error": None, "recovery_key": recovery_key}

        # ── password_only ────────────────────────────────────────────────
        # (mode == "password_only")
        salt = generate_salt()
        if not self.storage.save_salt(salt):
            return _fail("Could not save salt file.")

        system_key = create_system_key(salt)
        system_fernet = Fernet(system_key)

        encrypted_username = system_fernet.encrypt(username.encode())
        if not self.storage.save_master_username(encrypted_username):
            return _fail("Could not save username file.")

        password_hash = hash_password(password, salt)
        encrypted_hash = system_fernet.encrypt(binascii.hexlify(password_hash))
        if not self.storage.save_password_hash(encrypted_hash):
            return _fail("Could not save password hash file.")

        self.auth.fernet = create_user_key(username, password, salt)
        self.session.set_authenticated(username)

        ks = SecureKeyStore(salt=salt, logger=self.logger)
        self.auth.keystore = ks
        ks.store_auth_mode("password_only")

        return {"success": True, "error": None, "recovery_key": None}

    def create_backup(self) -> Optional[str]:
        try:
            return self.storage.create_backup()
        except Exception as exc:
            log.error("Failed to create backup: %s", exc)
            return None

    def get_storage_info(self) -> dict:
        try:
            return self.storage.get_storage_info()
        except Exception as exc:
            log.error("Failed to get storage info: %s", exc)
            return {"error": str(exc)}
