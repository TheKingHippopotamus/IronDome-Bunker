#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Authentication module for IronDome"""

import getpass
import binascii
import secrets
from cryptography.fernet import Fernet
from password_manager.encryption import hash_password, create_system_key, create_user_key, generate_salt
from password_manager.utils import get_validated_input, get_machine_info
from password_manager.biometric import BiometricAuth
from password_manager.keystore import SecureKeyStore

class AuthManager:
    """Manages authentication for IronDome"""

    def __init__(self, storage, session, logger=None):
        """
        Initialize the authentication manager

        Args:
            storage: PasswordStorage instance
            session: SessionManager instance
            logger: Optional logger instance
        """
        self.storage = storage
        self.session = session
        self.logger = logger
        self.fernet = None
        self.biometric = BiometricAuth(logger)
        self.keystore = None  # Initialized after salt is available
    
    def setup_security_mode(self):
        """Let user choose their security level during first-time setup"""
        bio_available = self.biometric.is_available()
        bio_type = self.biometric.get_type()

        if bio_available:
            print(f"\n🛡️  {bio_type} detected on this device!")
            print("\nChoose your security level:")
            print(f"  1. {bio_type} Only — quick access, no password needed")
            print(f"  2. {bio_type} + Master Password — maximum security")
            print("  3. Master Password Only — traditional login")

            choice = input("\nSelect (1/2/3): ").strip()

            if choice == '1':
                return self._setup_biometric_only(bio_type)
            elif choice == '2':
                return self._setup_biometric_password(bio_type)
            else:
                return self._setup_password_only()
        else:
            print("\nNo biometric hardware detected. Using password authentication.")
            return self._setup_password_only()

    def _setup_biometric_only(self, bio_type):
        """Setup biometric-only authentication"""
        print(f"\n--- {bio_type} Only Setup ---")
        print(f"Verify your identity with {bio_type} to begin:")

        if not self.biometric.authenticate(f"IronDome setup - verify {bio_type}"):
            print(f"❌ {bio_type} verification failed. Falling back to password setup.")
            return self._setup_password_only()

        # Generate a random Fernet key — this IS the encryption key
        salt = generate_salt()
        if not self.storage.save_salt(salt):
            print("❌ Error: Could not save salt file.")
            return False

        # Init keystore with salt
        self.keystore = SecureKeyStore(salt=salt, logger=self.logger)

        # Generate and store the master key in OS keychain
        master_key = self.keystore.generate_fernet_key()
        if not self.keystore.store_master_key(master_key):
            print("❌ Error: Could not store key in system keychain.")
            return self._setup_password_only()

        # Store auth mode
        self.keystore.store_auth_mode("biometric_only")

        # Generate recovery key
        recovery_key = self.keystore.generate_recovery_key()
        self.keystore.store_recovery_hash(recovery_key)

        print("\n" + "=" * 50)
        print("⚠️  SAVE YOUR RECOVERY KEY — shown only once!")
        print("=" * 50)
        print(f"\n   {recovery_key}\n")
        print("If your biometric hardware fails, this key")
        print("is the ONLY way to access your vault.")
        print("=" * 50)
        input("\nPress Enter after saving your recovery key...")

        # Create a system key entry (for compatibility — store a placeholder username)
        system_key = create_system_key(salt)
        system_fernet = Fernet(system_key)

        # Store a placeholder username encrypted (for master_account_exists() check)
        username = f"bio_{bio_type.lower().replace(' ', '_')}"
        encrypted_username = system_fernet.encrypt(username.encode())
        self.storage.save_master_username(encrypted_username)

        # Store a placeholder hash (not used for auth in this mode)
        placeholder_hash = hash_password("biometric_only_placeholder", salt)
        encrypted_hash = system_fernet.encrypt(binascii.hexlify(placeholder_hash))
        self.storage.save_password_hash(encrypted_hash)

        # Set up Fernet for password database
        self.fernet = Fernet(master_key)
        self.session.set_authenticated(username)

        print(f"✅ {bio_type} vault created successfully!")
        return True

    def _setup_biometric_password(self, bio_type):
        """Setup biometric + password authentication"""
        print(f"\n--- {bio_type} + Password Setup ---")
        print(f"Verify your identity with {bio_type} first:")

        if not self.biometric.authenticate(f"IronDome setup - verify {bio_type}"):
            print(f"❌ {bio_type} verification failed. Falling back to password only.")
            return self._setup_password_only()

        # Now create standard master account (username + password)
        result = self.create_master_account()
        if not result:
            return False

        # Store auth mode in keychain
        salt = self.storage.load_salt()
        self.keystore = SecureKeyStore(salt=salt, logger=self.logger)
        self.keystore.store_auth_mode("biometric_password")

        # Generate recovery key
        recovery_key = self.keystore.generate_recovery_key()
        self.keystore.store_recovery_hash(recovery_key)

        print("\n" + "=" * 50)
        print("⚠️  SAVE YOUR RECOVERY KEY — shown only once!")
        print("=" * 50)
        print(f"\n   {recovery_key}\n")
        print("Emergency access if biometric hardware fails.")
        print("=" * 50)
        input("\nPress Enter after saving your recovery key...")

        print(f"✅ {bio_type} + Password vault created!")
        return True

    def _setup_password_only(self):
        """Setup traditional password-only authentication"""
        result = self.create_master_account()
        if result:
            salt = self.storage.load_salt()
            self.keystore = SecureKeyStore(salt=salt, logger=self.logger)
            self.keystore.store_auth_mode("password_only")
        return result

    def authenticate_biometric(self):
        """Authenticate using biometric + optional password based on auth mode"""
        salt = self.storage.load_salt()
        if not salt:
            print("❌ Error: Salt file missing.")
            return False

        self.keystore = SecureKeyStore(salt=salt, logger=self.logger)
        auth_mode = self.keystore.get_auth_mode()

        if auth_mode == "biometric_only":
            return self._auth_biometric_only(salt)
        elif auth_mode == "biometric_password":
            return self._auth_biometric_password(salt)
        else:
            # password_only or unknown — fall through to standard auth
            return self.authenticate_master_account()

    # Maximum biometric retry attempts before forcing recovery-key path.
    _MAX_BIOMETRIC_RETRIES = 3

    def _auth_biometric_only(self, salt, _attempt: int = 1):
        """Authenticate with biometric only"""
        bio_type = self.biometric.get_type() or "Biometric"

        if not self.biometric.is_available():
            print(f"⚠️ {bio_type} not available. Use recovery key?")
            return self._recovery_flow(salt)

        print(f"\n🔐 Authenticate with {bio_type}:")

        if not self.biometric.authenticate("IronDome vault access"):
            print(f"❌ {bio_type} failed.")
            remaining_retries = self._MAX_BIOMETRIC_RETRIES - _attempt
            if remaining_retries > 0:
                retry = input(
                    f"Try again (t) or use recovery key (r)? "
                    f"[{remaining_retries} attempt(s) remaining] "
                ).strip().lower()
                if retry == 't':
                    return self._auth_biometric_only(salt, _attempt=_attempt + 1)
            else:
                print(f"❌ Maximum biometric attempts reached.")
            return self._recovery_flow(salt)

        # Retrieve master key from keychain
        master_key = self.keystore.retrieve_master_key()
        if not master_key:
            print("❌ Could not retrieve vault key from system keychain.")
            return self._recovery_flow(salt)

        # Set up Fernet
        self.fernet = Fernet(master_key)

        # Get username from storage
        system_key = create_system_key(salt)
        system_fernet = Fernet(system_key)
        encrypted_username = self.storage.load_master_username()
        try:
            username = system_fernet.decrypt(encrypted_username).decode()
        except Exception:
            username = "user"

        self.session.set_authenticated(username)
        self.session.update_login_attempts(True)

        print(f"✅ {bio_type} verified. Welcome back!")
        return True

    def _auth_biometric_password(self, salt):
        """Authenticate with biometric gate + password"""
        bio_type = self.biometric.get_type() or "Biometric"

        if not self.biometric.is_available():
            print(f"⚠️ {bio_type} not available. Use recovery key?")
            choice = input("Recovery key (r) or password only (p)? ").strip().lower()
            if choice == 'r':
                return self._recovery_flow(salt)
            else:
                return self.authenticate_master_account()

        print(f"\n🔐 Step 1: {bio_type} verification")

        if not self.biometric.authenticate("IronDome - first factor"):
            print(f"❌ {bio_type} failed. Access denied.")
            return False

        print(f"✅ {bio_type} verified.")
        print("🔑 Step 2: Enter master password")

        # Now do standard password auth
        return self.authenticate_master_account()

    def _recovery_flow(self, salt):
        """Emergency recovery using recovery key"""
        print("\n--- Emergency Recovery ---")
        # Use getpass to suppress echo — recovery keys are high-value secrets
        # and must not appear in terminal history or over-the-shoulder view.
        recovery_input = getpass.getpass("Enter your recovery key: ").strip()

        if not self.keystore.verify_recovery_key(recovery_input):
            print("❌ Invalid recovery key.")
            return False

        auth_mode = self.keystore.get_auth_mode()

        if auth_mode == "biometric_only":
            # Retrieve master key from keychain (recovery key verified identity)
            master_key = self.keystore.retrieve_master_key()
            if not master_key:
                print("❌ Could not retrieve vault key. Vault may need to be reset.")
                return False

            self.fernet = Fernet(master_key)
            system_key = create_system_key(salt)
            system_fernet = Fernet(system_key)
            encrypted_username = self.storage.load_master_username()
            try:
                username = system_fernet.decrypt(encrypted_username).decode()
            except Exception:
                username = "user"

            self.session.set_authenticated(username)
            print("✅ Recovery successful. Welcome back!")
            return True
        else:
            # For biometric+password mode, recovery bypasses biometric gate
            return self.authenticate_master_account()

    def create_master_account(self):
        """
        Create a new master username and password
        
        Returns:
            True if account was created successfully, False otherwise
        """
        print("\n=== Create Master Credentials ===")
        
        # Get and validate master username
        while True:
            username = input("Create master username (min 4 characters): ").strip()
            if len(username) < 4:
                print("⚠️ Username must be at least 4 characters long.")
                continue
            break
        
        # Get and validate master password
        while True:
            password = getpass.getpass("Create master password (min 8 characters): ")
            if len(password) < 8:
                print("⚠️ Master password must be at least 8 characters long.")
                continue
                
            confirm_password = getpass.getpass("Confirm master password: ")
            if password != confirm_password:
                print("⚠️ Passwords do not match. Please try again.")
                continue
                
            break
        
        # Create and save salt
        salt = generate_salt()
        if not self.storage.save_salt(salt):
            print("❌ Error: Could not save salt file.")
            return False
        
        # Create encryption key for securing the username and password hash
        system_key = create_system_key(salt)
        system_fernet = Fernet(system_key)
        
        # Encrypt and save username
        encrypted_username = system_fernet.encrypt(username.encode())
        if not self.storage.save_master_username(encrypted_username):
            print("❌ Error: Could not save username file.")
            return False
        
        # Hash password with salt and encrypt the hash
        password_hash = hash_password(password, salt)
        encrypted_hash = system_fernet.encrypt(binascii.hexlify(password_hash))
        if not self.storage.save_password_hash(encrypted_hash):
            print("❌ Error: Could not save password hash file.")
            return False
        
        # Set up encryption key for passwords database
        self.fernet = create_user_key(username, password, salt)
        
        # Update session
        self.session.set_authenticated(username)
        
        print("✅ Master account created successfully!")
        return True
    
    def authenticate_master_account(self):
        """
        Authenticate with existing master username and password
        
        Returns:
            True if authentication successful, False otherwise
        """
        # Check if login is allowed based on previous attempts
        login_check = self.session.check_login_attempts()
        if not login_check["allowed"]:
            print(f"\n⛔ {login_check['message']}")
            return False
            
        print("\n=== IronDome Login ===")
        
        # Load salt
        salt = self.storage.load_salt()
        if not salt:
            print("❌ Error: Salt file missing. IronDome needs to be reset.")
            return False
            
        # Create system key for decryption
        system_key = create_system_key(salt)
        system_fernet = Fernet(system_key)
        
        # Read encrypted username
        encrypted_username = self.storage.load_master_username()
        if not encrypted_username:
            print("❌ Error: Could not read master username.")
            self.session.update_login_attempts(False)
            return False
            
        try:
            stored_username = system_fernet.decrypt(encrypted_username).decode()
        except Exception as e:
            print(f"❌ Error: Could not decrypt master username: {e}")
            self.session.update_login_attempts(False)
            return False
        
        # Get max allowed attempts based on previous failures
        machine_info = get_machine_info()
        login_data = self.session._load_login_attempts()
        machine_id = machine_info["mac_address"]
        
        if machine_id in login_data:
            machine_data = login_data[machine_id]
            previous_lockouts = machine_data.get("previous_lockouts", 0)
            # Decrease max attempts based on previous lockouts
            max_attempts = max(1, self.session.max_login_attempts - previous_lockouts)
        else:
            max_attempts = self.session.max_login_attempts
        
        # Ask for login credentials
        attempts = 0
        
        while attempts < max_attempts:
            username = input("Enter username: ").strip()
            password = getpass.getpass("Enter password: ")
            attempts += 1
            
            # Check username first without revealing if it's correct
            if username != stored_username:
                # Don't reveal that username is wrong, just say credentials are invalid
                remaining = max_attempts - attempts
                login_attempt = self.session.update_login_attempts(False)
                
                # Use remaining from login tracking
                if "remaining_attempts" in login_attempt:
                    remaining = login_attempt["remaining_attempts"]
                
                if remaining > 0:
                    print(f"⚠️ Invalid credentials. {remaining} attempt{'s' if remaining != 1 else ''} remaining.")
                else:
                    print("⚠️ Invalid credentials. No attempts remaining.")
                    print(f"Your device has been locked out for {self.session.lockout_duration // 60} minutes.")
                return False
            
            # Hash the provided password
            provided_hash = hash_password(password, salt)
            
            # Read and decrypt stored hash
            encrypted_hash = self.storage.load_password_hash()
            if not encrypted_hash:
                print("❌ Error: Could not read password hash.")
                self.session.update_login_attempts(False)
                return False
                
            try:
                stored_hash = binascii.unhexlify(system_fernet.decrypt(encrypted_hash))
            except Exception as e:
                print(f"❌ Error: Could not decrypt password hash: {e}")
                self.session.update_login_attempts(False)
                return False
            
            # Compare hashes using constant-time comparison to prevent timing attacks
            if secrets.compare_digest(provided_hash, stored_hash):
                # Set up encryption key for passwords database
                self.fernet = create_user_key(username, password, salt)
                self.session.set_authenticated(username)
                
                # Update login attempt tracking on success
                self.session.update_login_attempts(True)
                
                print(f"✅ Login successful. Welcome back, {username}!")
                return True
            else:
                # Password is wrong
                login_attempt = self.session.update_login_attempts(False)
                
                # Get remaining attempts from login tracking
                if "remaining_attempts" in login_attempt:
                    remaining = login_attempt["remaining_attempts"]
                else:
                    remaining = max_attempts - attempts
                
                if remaining > 0:
                    print(f"⚠️ Invalid password. {remaining} attempt{'s' if remaining != 1 else ''} remaining.")
                else:
                    print("⚠️ Invalid password. No attempts remaining.")
                    print(f"Your device has been locked out for {self.session.lockout_duration // 60} minutes.")
                    return False
        
        print("❌ Too many failed login attempts. Your device has been locked out.")
        return False
    
    def require_auth_for_sensitive_action(self, action_name):
        """
        Require re-authentication for sensitive actions.

        Biometric modes use biometric re-auth first; password-only mode uses
        a password prompt.  For biometric+password mode, biometric failure
        falls through to password.

        Args:
            action_name: Description of the action requiring re-authentication

        Returns:
            True if re-authentication successful, False otherwise
        """
        if not self.session.session_authenticated:
            print("❌ You must be logged in to perform this action.")
            return False

        self.session.update_activity_time()
        print(f"\n⚠️ {action_name} is a sensitive operation that requires re-authentication.")

        # Load salt
        salt = self.storage.load_salt()
        if not salt:
            print("❌ Error: Salt file missing.")
            return False

        if self.keystore is None:
            self.keystore = SecureKeyStore(salt=salt, logger=self.logger)

        auth_mode = self.keystore.get_auth_mode()

        # Biometric re-auth for biometric modes
        if auth_mode in ("biometric_only", "biometric_password") and self.biometric.is_available():
            bio_type = self.biometric.get_type() or "Biometric"
            print(f"Verify with {bio_type} to continue:")
            if self.biometric.authenticate(f"IronDome - {action_name}"):
                return True
            print(f"❌ {bio_type} failed.")
            if auth_mode == "biometric_only":
                return False
            # Fall through to password for biometric_password mode

        # Password re-auth
        password = getpass.getpass("Enter your master password to continue: ")
        provided_hash = hash_password(password, salt)

        system_key = create_system_key(salt)
        system_fernet = Fernet(system_key)

        encrypted_hash = self.storage.load_password_hash()
        if not encrypted_hash:
            print("❌ Error: Could not read password hash.")
            return False

        try:
            stored_hash = binascii.unhexlify(system_fernet.decrypt(encrypted_hash))
        except Exception as e:
            print(f"❌ Error: Could not decrypt password hash: {e}")
            return False

        if secrets.compare_digest(provided_hash, stored_hash):
            return True
        else:
            print("❌ Invalid password. Action cancelled.")
            return False 