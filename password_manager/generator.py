#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Password generation module for IronDome"""

import secrets
from password_manager.constants import LOWERCASE, UPPERCASE, DIGITS, SPECIAL_CHARS

_sysrand = secrets.SystemRandom()

def create_diverse_password(length, all_chars, **char_types):
    """
    Create a password with at least one character from each required type

    Args:
        length: Length of password to generate
        all_chars: List of all allowed characters
        **char_types: Keyword arguments for character types to include

    Returns:
        Generated password string
    """
    password = ""

    # Start with one character from each required type
    if char_types.get('use_lowercase', False) and LOWERCASE:
        password += secrets.choice(LOWERCASE)

    if char_types.get('use_uppercase', False) and UPPERCASE:
        password += secrets.choice(UPPERCASE)

    if char_types.get('use_digits', False) and DIGITS:
        password += secrets.choice(DIGITS)

    if char_types.get('use_special', False) and SPECIAL_CHARS:
        password += secrets.choice(SPECIAL_CHARS)

    # Fill remaining characters randomly
    while len(password) < length:
        password += secrets.choice(all_chars)

    # Shuffle the password characters for randomness
    password_list = list(password)
    _sysrand.shuffle(password_list)
    password = ''.join(password_list)

    return password

def calculate_password_strength(password):
    """
    Calculate password strength score

    Args:
        password: Password to evaluate

    Returns:
        String rating of password strength
    """
    score = 0

    # Length score
    if len(password) >= 16:
        score += 30
    elif len(password) >= 12:
        score += 20
    elif len(password) >= 8:
        score += 10

    # Character diversity score
    if any(c in LOWERCASE for c in password):
        score += 10
    if any(c in UPPERCASE for c in password):
        score += 15
    if any(c in DIGITS for c in password):
        score += 15
    if any(c in SPECIAL_CHARS for c in password):
        score += 20

    # Rating
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Very Strong"
    elif score >= 40:
        return "Strong"
    elif score >= 25:
        return "Medium"
    else:
        return "Weak"

def generate_password(length=15, use_special=True, use_uppercase=True, use_digits=True, logger=None):
    """
    Generate a strong random password with selected character types

    Args:
        length: Length of password to generate
        use_special: Whether to include special characters
        use_uppercase: Whether to include uppercase letters
        use_digits: Whether to include digits
        logger: Optional logger instance

    Returns:
        Dictionary with password info or None if invalid input
    """
    # Log password generation (without the actual password)
    if logger:
        logger.info(f"Generating password (length={length}, special={use_special}, uppercase={use_uppercase}, digits={use_digits})")

    # Validate inputs
    if not isinstance(length, int) or length <= 0:
        print("⚠️ Invalid length. Using default length of 15.")
        length = 15

    # Build character set based on options
    all_chars = LOWERCASE.copy()

    if use_uppercase:
        all_chars += UPPERCASE

    if use_digits:
        all_chars += DIGITS

    if use_special:
        all_chars += SPECIAL_CHARS

    # Ensure we have enough character diversity
    if len(all_chars) < 30:
        print("Warning: Limited character set may reduce password strength")

    # Create password with required character types
    password = create_diverse_password(
        length,
        all_chars,
        use_lowercase=True,
        use_uppercase=use_uppercase,
        use_digits=use_digits,
        use_special=use_special
    )

    # Calculate strength
    strength = calculate_password_strength(password)

    return {
        'password': password,
        'strength': strength,
        'length': len(password),
        'character_types': {
            'lowercase': any(c in LOWERCASE for c in password),
            'uppercase': any(c in UPPERCASE for c in password),
            'digits': any(c in DIGITS for c in password),
            'special': any(c in SPECIAL_CHARS for c in password)
        }
    }
