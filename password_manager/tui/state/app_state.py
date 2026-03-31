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
