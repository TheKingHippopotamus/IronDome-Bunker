#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Encryption utilities for the Secure Password Manager"""

import base64
import getpass
import os
import uuid
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# OWASP 2023 recommended minimum for PBKDF2-HMAC-SHA256
PBKDF2_ITERATIONS = 600_000

def hash_password(password, salt):
    """
    Create a secure hash of the password using PBKDF2-HMAC-SHA256

    Args:
        password: The password string
        salt: The salt bytes

    Returns:
        Password hash digest (32 bytes)
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode())

def get_machine_id():
    """
    Get a unique machine identifier, or generate a persistent fallback

    Returns:
        String identifier for the current machine
    """
    try:
        # Try to get machine-specific identifier
        if os.path.exists('/etc/machine-id'):
            with open('/etc/machine-id', 'r') as f:
                return f.read().strip()
        elif os.path.exists('/var/lib/dbus/machine-id'):
            with open('/var/lib/dbus/machine-id', 'r') as f:
                return f.read().strip()
        else:
            # Fallback to username and hostname
            return f"{getpass.getuser()}@{os.uname().nodename}"
    except Exception:
        # Generate a persistent device ID instead of using a hardcoded key
        device_id_path = os.path.join(os.path.expanduser("~"), ".password_manager", ".device_id")
        try:
            if os.path.exists(device_id_path):
                with open(device_id_path, 'r') as f:
                    return f.read().strip()
            else:
                device_id = str(uuid.uuid4())
                os.makedirs(os.path.dirname(device_id_path), exist_ok=True)
                with open(device_id_path, 'w') as f:
                    f.write(device_id)
                return device_id
        except Exception:
            # Last resort: use a combination that's at least unique per user home dir
            return f"fallback-{os.path.expanduser('~')}"

def create_system_key(salt):
    """
    Create a system-specific key for encrypting master credentials

    Args:
        salt: Salt bytes for key derivation

    Returns:
        URL-safe base64 encoded key
    """
    # Use machine-specific information plus salt to create a key
    machine_id = get_machine_id()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )

    key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
    return key

def create_user_key(username, password, salt):
    """
    Create an encryption key based on username and password

    Args:
        username: The username string
        password: The password string
        salt: Salt bytes for key derivation

    Returns:
        Fernet encryption key object
    """
    # Combine username and password for KDF input using a length-prefixed
    # encoding to prevent separator-collision attacks.  A bare ":" separator
    # (e.g. "a:bc" + "d" vs "a" + ":bcd") allows two distinct credential
    # pairs to derive an identical KDF input.  Encoding the username length
    # as a zero-padded 8-byte prefix makes the boundary unambiguous.
    username_bytes = username.encode()
    password_bytes = password.encode()
    combined_key = (
        len(username_bytes).to_bytes(8, "big")
        + username_bytes
        + password_bytes
    )

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )

    key = base64.urlsafe_b64encode(kdf.derive(combined_key))
    return Fernet(key)

def generate_salt():
    """
    Generate a random salt for password hashing

    Returns:
        Random salt bytes
    """
    return os.urandom(16)
