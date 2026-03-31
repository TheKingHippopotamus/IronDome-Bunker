#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Main manager module for the Secure Password Manager"""

import os
import time
import getpass
from password_manager.storage import PasswordStorage
from password_manager.auth import AuthManager
from password_manager.session import SessionManager
from password_manager.logger import setup_logger
from password_manager.generator import generate_password
from password_manager.utils import get_validated_input, get_validated_int, extract_domain_name

class SecurePasswordManager:
    """Main password manager class that integrates all components"""
    
    def __init__(self):
        """Initialize the password manager with all components"""
        # Set up storage directory and files
        self.data_dir = os.path.join(os.path.expanduser("~"), ".password_manager")
        
        # Set up logger
        self.log_file = os.path.join(self.data_dir, "password_manager.log")
        self.logger = None
        
        # Set up storage, session and auth managers
        self.storage = PasswordStorage(self.data_dir, self.logger)
        self.login_attempts_file = self.storage.login_attempts_file
        
        # Now that storage has created the directories, set up logger
        self.logger = setup_logger(self.log_file)
        
        # Update logger reference in storage
        self.storage.logger = self.logger
        
        # Create session and auth managers
        self.session = SessionManager(self.login_attempts_file, self.logger)
        self.auth = AuthManager(self.storage, self.session, self.logger)
        
        # Initialize master account
        self.initialize_master_account()
        
        # Log information only if authenticated
        if self.session.session_authenticated:
            self.logger.info(f"Password Manager initialized. Data directory: {self.data_dir}")
    
    def initialize_master_account(self):
        """Set up master account with security level selection, or authenticate"""
        account_exists = self.storage.master_account_exists()

        if account_exists:
            if not os.path.isfile(self.login_attempts_file):
                with open(self.login_attempts_file, 'w') as f:
                    f.write('{}')

            # Check auth mode to determine login flow
            salt = self.storage.load_salt()
            if salt:
                from password_manager.keystore import SecureKeyStore
                keystore = SecureKeyStore(salt=salt, logger=self.logger)
                auth_mode = keystore.get_auth_mode()
                self.auth.keystore = keystore
            else:
                auth_mode = None

            if auth_mode in ("biometric_only", "biometric_password"):
                # Use biometric auth flow
                login_check = self.session.check_login_attempts()
                if login_check["allowed"]:
                    self.auth.authenticate_biometric()
                else:
                    print(f"\n⛔ {login_check['message']}")
            else:
                # Standard password login
                login_check = self.session.check_login_attempts()
                if login_check["allowed"]:
                    print("\nMaster account exists. Please login.")
                    self.auth.authenticate_master_account()
                else:
                    print(f"\n⛔ {login_check['message']}")
        else:
            print("\nWelcome! Let's set up your secure vault.")
            self.auth.setup_security_mode()
    
    def generate_password(self, length=15, use_special=True, use_uppercase=True, use_digits=True):
        """
        Generate a strong random password with selected character types
        
        Args:
            length: Length of password to generate
            use_special: Whether to include special characters
            use_uppercase: Whether to include uppercase letters
            use_digits: Whether to include digits
            
        Returns:
            Dictionary with password info or None if not authenticated
        """
        # Validate session
        if not self.session.session_authenticated:
            print("❌ You must be logged in to generate passwords.")
            return None
            
        self.session.update_activity_time()
        
        return generate_password(length, use_special, use_uppercase, use_digits, self.logger)
    
    def save_password(self, username, website, password, notes=""):
        """
        Save a password to the encrypted storage file
        
        Args:
            username: Username for the stored password
            website: Website or service name
            password: Password to store
            notes: Optional notes
            
        Returns:
            True if successful, False otherwise
        """
        # Validate session
        if not self.session.session_authenticated:
            print("❌ You must be logged in to save passwords.")
            return False
            
        self.session.update_activity_time()
            
        # Validate inputs
        if not username or not website or not password:
            print("❌ Error: Username, website, and password are required.")
            return False
            
        if not self.auth.fernet:
            print("❌ Error: Encryption not initialized. Can't save password.")
            return False
        
        # Load existing passwords
        passwords = self.load_passwords()
        
        # Create new password entry
        entry = {
            'username': username,
            'website': website,
            'password': password,
            'notes': notes,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Check if this entry would be a duplicate
        for existing in passwords:
            if (existing['username'] == username and 
                existing['website'] == website):
                replace = get_validated_input(
                    "Entry already exists. Replace? (y/n): ", 
                    valid_options=['y', 'n'], 
                    default='n',
                    logger=self.logger
                )
                if replace != 'y':
                    print("Password not saved.")
                    return False
                else:
                    passwords.remove(existing)
                    self.logger.info(f"Replaced existing password for {username} at {website}")
                    break
        
        # Add the new entry
        passwords.append(entry)
        
        # Encrypt and save
        if self.storage.save_passwords(passwords, self.auth.fernet):
            # Log but don't include the password
            self.logger.info(f"Saved password for {username} at {website}")
            
            print(f"✅ Password saved successfully for {username} at {website}")
            return True
        else:
            return False
    
    def load_passwords(self):
        """
        Load and decrypt passwords from the storage file
        
        Returns:
            List of password dictionaries or empty list if not authenticated
        """
        # Validate session
        if not self.session.session_authenticated:
            print("❌ You must be logged in to access passwords.")
            return []
            
        self.session.update_activity_time()
            
        if not self.auth.fernet:
            print("❌ Error: Encryption not initialized. Can't load passwords.")
            return []
        
        return self.storage.load_passwords(self.auth.fernet)
    
    def find_password(self, search_term):
        """
        Search for passwords by username or website
        
        Args:
            search_term: Term to search for
            
        Returns:
            List of matching password entries
        """
        # Validate session
        if not self.session.session_authenticated:
            print("❌ You must be logged in to search passwords.")
            return []
            
        self.session.update_activity_time()
        
        # Log the search
        self.logger.info(f"Searching for passwords with term: {search_term}")
            
        if not search_term:
            print("Please enter a search term.")
            return []
            
        # Require at least 3 characters for search
        if len(search_term) < 3:
            print("⚠️ Search term must be at least 3 characters long.")
            return []
            
        passwords = self.load_passwords()
        results = []
        
        search_term = search_term.lower()
        
        for entry in passwords:
            # Extract domain name from website URL
            website = entry['website']
            domain = extract_domain_name(website).lower()
            
            # Extract username part (before @) from email addresses
            username = entry['username'].lower()
            username_part = username.split('@')[0] if '@' in username else username
            
            # Check if search term matches:
            # 1. The extracted domain name of the website
            # 2. The username part (before @) of the email
            if (search_term == domain or  # Exact match for domain
                domain.startswith(search_term) or  # Domain starts with search term
                search_term in username_part):  # Search term in username part
                results.append(entry)
        
        # Log search results count (but not the actual results)
        self.logger.info(f"Found {len(results)} results for search term: {search_term}")
        
        return results
    
    def list_websites(self):
        """
        List all websites in the password store
        
        Returns:
            Sorted list of website names
        """
        # Validate session
        if not self.session.session_authenticated:
            print("❌ You must be logged in to list websites.")
            return []
            
        self.session.update_activity_time()
            
        passwords = self.load_passwords()
        websites = set()
        
        for entry in passwords:
            websites.add(entry['website'])
        
        return sorted(list(websites))
    
    def delete_password(self, username, website):
        """
        Delete a specific password entry
        
        Args:
            username: Username of the entry to delete
            website: Website of the entry to delete
            
        Returns:
            True if successful, False otherwise
        """
        # Validate session and require re-authentication
        if not self.auth.require_auth_for_sensitive_action("Password deletion"):
            return False
            
        if not username or not website:
            print("Username and website are required.")
            return False
            
        passwords = self.load_passwords()
        initial_count = len(passwords)
        
        # Find and remove matching entries
        passwords = [entry for entry in passwords 
                    if not (entry['username'] == username and 
                           entry['website'] == website)]
        
        if len(passwords) < initial_count:
            # Confirm deletion
            confirm = get_validated_input(
                f"Are you sure you want to delete password for {username} at {website}? (yes/no): ",
                valid_options=['yes', 'no'],
                default='no',
                logger=self.logger
            )
            
            if confirm != 'yes':
                print("Deletion cancelled.")
                self.logger.info(f"Password deletion cancelled for {username} at {website}")
                return False
                
            # Save the updated list
            if self.storage.save_passwords(passwords, self.auth.fernet):
                self.logger.info(f"Deleted password for {username} at {website}")
                print(f"✅ Deleted password for {username} at {website}")
                return True
            else:
                return False
        else:
            self.logger.warning(f"Attempted to delete non-existent password for {username} at {website}")
            print(f"No matching entry found for {username} at {website}")
            return False
    
    def backup_passwords(self, backup_path=None):
        """
        Create a backup of the encrypted password file
        
        Args:
            backup_path: Optional custom backup path
            
        Returns:
            True if backup was successful, False otherwise
        """
        # Validate session
        if not self.session.session_authenticated:
            print("❌ You must be logged in to create backups.")
            return False
            
        self.session.update_activity_time()
            
        return self.storage.create_backup(backup_path) is not None
    
    def run_interactive_menu(self):
        """Run an interactive menu for the password manager"""
        while True:
            # Check if session is authenticated
            if not self.session.session_authenticated:
                auth_result = self.auth.authenticate_master_account()
                if not auth_result:
                    print("Exiting Password Manager due to authentication failure.")
                    break
                continue  # Show menu after successful authentication
            
            # Update activity time
            self.session.update_activity_time()
            
            # Show the main menu
            print("\n=== Password Manager ===")
            print(f"Logged in as: {self.session.username}")
            print("1. Generate a new password")
            print("2. Save a password")
            print("3. Find passwords")
            print("4. List all websites")
            print("5. Delete a password")
            print("6. Create backup")
            print("7. Show storage location")
            print("8. Logout")
            print("9. Exit")
            
            choice = get_validated_input(
                "\nChoose an option (1-9): ", 
                valid_options=['1', '2', '3', '4', '5', '6', '7', '8', '9'],
                allow_back=False,  # Can't go back from main menu
                logger=self.logger
            )
            
            # Log menu choice
            self.logger.debug(f"Menu option selected: {choice}")
            
            if choice == '1':
                self._handle_generate_password()
            elif choice == '2':
                self._handle_save_password()
            elif choice == '3':
                self._handle_find_password()
            elif choice == '4':
                self._handle_list_websites()
            elif choice == '5':
                self._handle_delete_password()
            elif choice == '6':
                self.backup_passwords()
            elif choice == '7':
                self._handle_show_storage()
            elif choice == '8':
                print("Logging out...")
                self.session.logout()
            elif choice == '9':
                print("Exiting Password Manager.")
                if self.session.username:
                    self.logger.info(f"User {self.session.username} exited the application")
                break
    
    def _handle_generate_password(self):
        """Handle password generation flow with back option"""
        # Validate session
        if not self.session.session_authenticated:
            print("❌ You must be logged in to generate passwords.")
            return
            
        self.session.update_activity_time()
        
        # Get password length
        length = get_validated_int(
            "Password length (recommended 15+): ", 
            min_value=4, 
            default=15,
            logger=self.logger
        )
        if length == '_BACK_':
            return
        
        # Get special characters option
        use_special = get_validated_input(
            "Include special characters (!@#$%^*)()? (y/n): ", 
            valid_options=['y', 'n'], 
            default='y',
            logger=self.logger
        )
        if use_special == '_BACK_':
            return
        use_special = (use_special == 'y')
        
        # Get uppercase option
        use_uppercase = get_validated_input(
            "Include uppercase letters? (y/n): ", 
            valid_options=['y', 'n'], 
            default='y',
            logger=self.logger
        )
        if use_uppercase == '_BACK_':
            return
        use_uppercase = (use_uppercase == 'y')
        
        # Get digits option
        use_digits = get_validated_input(
            "Include digits? (y/n): ", 
            valid_options=['y', 'n'], 
            default='y',
            logger=self.logger
        )
        if use_digits == '_BACK_':
            return
        use_digits = (use_digits == 'y')
        
        # Generate password
        pwd_info = self.generate_password(
            length, use_special, use_uppercase, use_digits)
        
        if not pwd_info:  # If generation failed (e.g. session expired)
            return
            
        print(f"\n🔑 Generated password: {pwd_info['password']}")
        print(f"🔒 Strength: {pwd_info['strength']}")
        
        # Get save option
        save_option = get_validated_input(
            "Save this password? (y/n): ", 
            valid_options=['y', 'n'], 
            default='n',
            logger=self.logger
        )
        if save_option == '_BACK_':
            return
        
        if save_option == 'y':
            # Get username
            while True:
                username = input("Username (or 'b' to go back): ").strip()
                if username.lower() in ['b', 'back']:
                    return
                if username:
                    break
                print("⚠️ Username cannot be empty.")
            
            # Get website
            while True:
                website = input("Website/Service name (or 'b' to go back): ").strip()
                if website.lower() in ['b', 'back']:
                    return
                if website:
                    break
                print("⚠️ Website/Service name cannot be empty.")
            
            # Get notes
            notes = input("Notes (optional, or 'b' to go back): ")
            if notes.lower() in ['b', 'back']:
                return
            
            # Final confirmation
            confirm = get_validated_input(
                f"Confirm saving password for {username} at {website}? (y/n): ", 
                valid_options=['y', 'n'], 
                default='y',
                logger=self.logger
            )
            if confirm == '_BACK_':
                return
            
            if confirm == 'y':
                self.save_password(username, website, pwd_info['password'], notes)
            else:
                print("Password not saved.")
    
    def _handle_save_password(self):
        """Handle save password flow with back option"""
        # Validate session
        if not self.session.session_authenticated:
            print("❌ You must be logged in to save passwords.")
            return
            
        self.session.update_activity_time()
        
        # Get username
        while True:
            username = input("Username (or 'b' to go back): ").strip()
            if username.lower() in ['b', 'back']:
                return
            if username:
                break
            print("⚠️ Username cannot be empty.")
        
        # Get website
        while True:
            website = input("Website/Service name (or 'b' to go back): ").strip()
            if website.lower() in ['b', 'back']:
                return
            if website:
                break
            print("⚠️ Website/Service name cannot be empty.")
        
        # Get password
        while True:
            password = getpass.getpass("Password (or 'b' to go back): ")
            if password.lower() in ['b', 'back']:
                return
            if password:
                break
            print("⚠️ Password cannot be empty.")
        
        # Get notes
        notes = input("Notes (optional, or 'b' to go back): ")
        if notes.lower() in ['b', 'back']:
            return
        
        # Final confirmation
        confirm = get_validated_input(
            f"Confirm saving password for {username} at {website}? (y/n): ", 
            valid_options=['y', 'n'], 
            default='y',
            logger=self.logger
        )
        if confirm == '_BACK_':
            return
        
        if confirm == 'y':
            self.save_password(username, website, password, notes)
        else:
            print("Password not saved.")
    
    def _handle_find_password(self):
        """Handle find password flow with back option"""
        # Validate session
        if not self.session.session_authenticated:
            print("❌ You must be logged in to find passwords.")
            return
            
        self.session.update_activity_time()
        
        # Get search term
        while True:
            search_term = input("Search (username or website, or 'b' to go back): ").strip()
            if search_term.lower() in ['b', 'back']:
                return
            if search_term:
                break
            print("⚠️ Search term cannot be empty.")
        
        results = self.find_password(search_term)
        
        if results:
            print(f"\nFound {len(results)} results:")
            for idx, entry in enumerate(results, 1):
                print(f"{idx}. Website: {entry['website']}, Username: {entry['username']}")
            
            valid_indices = [str(i) for i in range(1, len(results) + 1)]
            show_idx = get_validated_input(
                "Show password by number (or Enter to go back): ", 
                valid_options=valid_indices + [''],
                default='',
                logger=self.logger
            )
            
            if show_idx == '_BACK_' or not show_idx:
                return
            
            # Re-authenticate to view password
            if not self.auth.require_auth_for_sensitive_action("Viewing password"):
                return
                
            entry = results[int(show_idx) - 1]
            print(f"\nWebsite: {entry['website']}")
            print(f"Username: {entry['username']}")
            print(f"Password: {entry['password']}")
            if entry.get('notes'):
                print(f"Notes: {entry['notes']}")
            print(f"Created on: {entry['created_at']}")
            
            # Log viewed password (but don't include the actual password)
            self.logger.info(f"Viewed password for {entry['username']} at {entry['website']}")
            
            # Pause before returning to menu
            input("\nPress Enter to continue...")
        else:
            print("No results found.")
    
    def _handle_list_websites(self):
        """Handle list websites flow with back option"""
        # Validate session
        if not self.session.session_authenticated:
            print("❌ You must be logged in to list websites.")
            return
            
        self.session.update_activity_time()
        
        websites = self.list_websites()
        if websites:
            print("\nList of saved websites/services:")
            for idx, site in enumerate(websites, 1):
                print(f"{idx}. {site}")
            print(f"\nTotal: {len(websites)} websites")
            
            self.logger.info(f"Listed {len(websites)} websites")
            
            # Pause before returning to menu
            input("\nPress Enter to continue...")
        else:
            print("No saved websites.")
    
    def _handle_delete_password(self):
        """Handle delete password flow with back option"""
        # Validate session
        if not self.session.session_authenticated:
            print("❌ You must be logged in to delete passwords.")
            return
            
        self.session.update_activity_time()
        
        # Get username
        while True:
            username = input("Username to delete (or 'b' to go back): ").strip()
            if username.lower() in ['b', 'back']:
                return
            if username:
                break
            print("⚠️ Username cannot be empty.")
        
        # Get website
        while True:
            website = input("Website/Service name (or 'b' to go back): ").strip()
            if website.lower() in ['b', 'back']:
                return
            if website:
                break
            print("⚠️ Website/Service name cannot be empty.")
        
        self.delete_password(username, website)
    
    def _handle_show_storage(self):
        """Handle show storage flow with back option"""
        # Validate session and require re-authentication
        if not self.auth.require_auth_for_sensitive_action("Viewing storage information"):
            return
        
        self.logger.info("Storage information displayed")
        
        storage_info = self.storage.get_storage_info()
        
        print("\nStorage Information:")
        print(f"Data directory: {storage_info['data_directory']}")
        print(f"Secrets directory: {storage_info['secrets_directory']}")
        print(f"Passwords file: {storage_info['passwords_file']}")
        print(f"Salt file: {storage_info['salt_file']}")
        print(f"Master username file: {storage_info['master_username_file']}")
        print(f"Master password hash file: {storage_info['master_password_hash_file']}")
        print(f"Login attempts file: {storage_info['login_attempts_file']}")
        print(f"Log file: {storage_info['log_file']}")
        print(f"Session timeout: {self.session.session_timeout//60} minutes")
        print(f"Lockout duration: {self.session.lockout_duration//60} minutes")
        
        if "password_file_size" in storage_info:
            print(f"Password file size: {storage_info['password_file_size']} bytes")
            print(f"Last modified: {storage_info['last_modified']}")
        
        # Pause before returning to menu
        input("\nPress Enter to continue...") 