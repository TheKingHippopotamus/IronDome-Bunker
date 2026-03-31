#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Constants for IronDome"""

# Define character sets for password generation
LOWERCASE = list("abcdefghijklmnopqrstuvwxyz")
UPPERCASE = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
DIGITS = list("0123456789")
SPECIAL_CHARS = list("!@#$%^&*()-_+=")

# Session and security constants
SESSION_TIMEOUT = 30 * 60  # 30 minutes
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_DURATION = 15 * 60  # 15 minutes 