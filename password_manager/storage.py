#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Storage utilities for IronDome"""

import os
import json
import time
import shutil

class PasswordStorage:
    """Handles storage operations for IronDome"""
    
    def __init__(self, data_dir, logger=None):
        """
        Initialize the storage handler
        
        Args:
            data_dir: Path to the data directory
            logger: Optional logger instance
        """
        self.data_dir = data_dir
        self.logger = logger
        
        # Set up secrets directory
        self.secrets_dir = os.path.join(self.data_dir, "secrets")
        
        # Set up file paths
        self.passwords_file = os.path.join(self.secrets_dir, ".passwords.enc")
        self.salt_file = os.path.join(self.secrets_dir, "salt.bin")
        self.username_file = os.path.join(self.secrets_dir, ".master_user.enc")
        self.password_hash_file = os.path.join(self.secrets_dir, ".master_hash.enc")
        self.login_attempts_file = os.path.join(self.secrets_dir, ".login_attempts.dat")
        self.log_file = os.path.join(self.data_dir, "password_manager.log")
        
        # Create data directory and secrets directory if they don't exist
        self._ensure_dirs_exist()
        
        # Migrate files from old location if needed
        self._migrate_files_if_needed()
    
    def _ensure_dirs_exist(self):
        """Create the data directory and secrets directory if they don't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"Created data directory at: {self.data_dir}")
            if self.logger:
                self.logger.info(f"Created data directory: {self.data_dir}")
                
        if not os.path.exists(self.secrets_dir):
            os.makedirs(self.secrets_dir, mode=0o700)  # Restricted permissions for secrets
            print(f"Created secrets directory at: {self.secrets_dir}")
            if self.logger:
                self.logger.info(f"Created secrets directory: {self.secrets_dir}")
    
    def _migrate_files_if_needed(self):
        """Migrate files from old locations to new locations if needed"""
        # Define old file paths
        old_paths = {
            "passwords": os.path.join(self.data_dir, ".passwords.enc"),
            "salt": os.path.join(self.data_dir, "salt.bin"),
            "username": os.path.join(self.data_dir, ".master_user.enc"),
            "password_hash": os.path.join(self.data_dir, ".master_hash.enc"),
            "login_attempts": os.path.join(self.data_dir, ".login_attempts.dat")
        }
        
        # Define new file paths
        new_paths = {
            "passwords": self.passwords_file,
            "salt": self.salt_file,
            "username": self.username_file,
            "password_hash": self.password_hash_file,
            "login_attempts": self.login_attempts_file
        }
        
        # Check if migration is needed and perform it
        for key, old_path in old_paths.items():
            if os.path.exists(old_path) and not os.path.exists(new_paths[key]):
                try:
                    shutil.copy2(old_path, new_paths[key])
                    if self.logger:
                        self.logger.info(f"Migrated {key} file to new location: {new_paths[key]}")
                    print(f"Migrated {key} file to: {new_paths[key]}")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error migrating {key} file: {e}")
                    print(f"Error migrating {key} file: {e}")
    
    def save_passwords(self, passwords, fernet):
        """
        Save passwords to encrypted storage
        
        Args:
            passwords: List of password dictionaries to save
            fernet: Fernet key object for encryption
            
        Returns:
            True if successful, False otherwise
        """
        try:
            encrypted_data = fernet.encrypt(json.dumps(passwords).encode())
            with open(self.passwords_file, 'wb') as f:
                f.write(encrypted_data)
            return True
        except Exception as e:
            error_msg = f"Error saving passwords: {e}"
            if self.logger:
                self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def load_passwords(self, fernet):
        """
        Load passwords from encrypted storage
        
        Args:
            fernet: Fernet key object for decryption
            
        Returns:
            List of password dictionaries or empty list on failure
        """
        # Check if passwords file exists
        if not os.path.exists(self.passwords_file):
            return []
        
        try:
            # Read and decrypt data
            with open(self.passwords_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data)
        except Exception as e:
            print(f"❌ Error: Failed to decrypt data: {e}")
            print("   This usually means credentials were incorrect.")
            return []
    
    def save_salt(self, salt):
        """
        Save salt to file
        
        Args:
            salt: Salt bytes to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving salt: {e}")
            return False
    
    def load_salt(self):
        """
        Load salt from file
        
        Returns:
            Salt bytes or None if file doesn't exist
        """
        if not os.path.exists(self.salt_file):
            return None
            
        try:
            with open(self.salt_file, 'rb') as f:
                return f.read()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading salt: {e}")
            return None
    
    def save_master_username(self, encrypted_username):
        """
        Save encrypted master username
        
        Args:
            encrypted_username: Encrypted username bytes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.username_file, 'wb') as f:
                f.write(encrypted_username)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving master username: {e}")
            return False
    
    def load_master_username(self):
        """
        Load encrypted master username
        
        Returns:
            Encrypted username bytes or None if file doesn't exist
        """
        if not os.path.exists(self.username_file):
            return None
            
        try:
            with open(self.username_file, 'rb') as f:
                return f.read()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading master username: {e}")
            return None
    
    def save_password_hash(self, encrypted_hash):
        """
        Save encrypted password hash
        
        Args:
            encrypted_hash: Encrypted password hash bytes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.password_hash_file, 'wb') as f:
                f.write(encrypted_hash)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving password hash: {e}")
            return False
    
    def load_password_hash(self):
        """
        Load encrypted password hash
        
        Returns:
            Encrypted password hash bytes or None if file doesn't exist
        """
        if not os.path.exists(self.password_hash_file):
            return None
            
        try:
            with open(self.password_hash_file, 'rb') as f:
                return f.read()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading password hash: {e}")
            return None
    
    def master_account_exists(self):
        """
        Check if master account files exist
        
        Returns:
            True if all necessary files exist, False otherwise
        """
        return (os.path.exists(self.username_file) and
                os.path.exists(self.password_hash_file) and
                os.path.exists(self.salt_file))
    
    def create_backup(self, backup_path=None):
        """
        Create a backup of the encrypted password file
        
        Args:
            backup_path: Optional custom backup path
            
        Returns:
            Path to backup file or None on failure
        """
        if not os.path.exists(self.passwords_file):
            print("No bunker data to fortify.")
            return None
        
        # Set up backups directory if it doesn't exist
        backups_dir = os.path.join(self.data_dir, "backups")
        if not os.path.exists(backups_dir):
            os.makedirs(backups_dir)
            if self.logger:
                self.logger.info(f"Created backups directory: {backups_dir}")
        
        # Create backup in the backups directory with a hidden filename
        if backup_path is None:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            backup_path = os.path.join(
                backups_dir, f".passwords_backup_{timestamp}.enc")
        
        try:
            # Copy the encrypted file
            with open(self.passwords_file, 'rb') as src:
                with open(backup_path, 'wb') as dest:
                    dest.write(src.read())
            
            if self.logger:
                self.logger.info(f"Dome fortified at: {backup_path}")
            print(f"✅ Dome fortified at: {backup_path}")
            return backup_path
        except Exception as e:
            error_msg = f"Error creating backup: {e}"
            if self.logger:
                self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return None
            
    def get_storage_info(self):
        """
        Get information about the storage files
        
        Returns:
            Dictionary with storage information
        """
        info = {
            "data_directory": self.data_dir,
            "secrets_directory": self.secrets_dir,
            "passwords_file": self.passwords_file,
            "salt_file": self.salt_file,
            "master_username_file": self.username_file,
            "master_password_hash_file": self.password_hash_file,
            "login_attempts_file": self.login_attempts_file,
            "log_file": self.log_file
        }
        
        # Add file size and modification time if passwords file exists
        if os.path.exists(self.passwords_file):
            size = os.path.getsize(self.passwords_file)
            info["password_file_size"] = size
            info["last_modified"] = time.ctime(os.path.getmtime(self.passwords_file))
            
        return info 