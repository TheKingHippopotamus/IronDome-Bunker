# Secure CLI Password Manager | Cybersecurity
& Python Engineering

A professional-grade, secure password management system that allows you to create, store, and manage passwords locally with multiple layers of encryption. All data is stored locally with advanced encryption, ensuring your sensitive information never leaves your device.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Security Architecture](#security-architecture)
- [Directory Structure](#directory-structure)
- [Advanced Usage](#advanced-usage)
- [Security Best Practices](#security-best-practices)
- [Technical Details](#technical-details)
- [Requirements](#requirements)
- [License](#license)
- [Screenshots and Demo](#screenshots-and-demo)

## Features

### Security Features
- **Military-grade AES-256 encryption** via Fernet symmetric encryption
- **Zero-knowledge architecture** - your master password is never stored, only a salted hash
- **Protection against brute force attacks** with adaptive account lockouts
- **Hardware-linked encryption** with machine-specific key derivation
- **Session protection** with automatic timeout after inactivity
- **Secure credential storage** with separate master username/password handling
- **File isolation** with sensitive data stored in a restricted permissions directory

### Management Features
- **Strong password generation** with customizable options:
  - Adjustable length (4-100+ characters)
  - Customizable character sets (lowercase, uppercase, numbers, special chars)
  - Real-time password strength evaluation
- **Comprehensive search capabilities** with domain and username matching
- **Secure backup system** with encrypted backups stored in a dedicated directory
- **Detailed logging** without sensitive data exposure
- **Automatic data migration** when file paths are updated

### User Experience
- **Command-line interface** with intuitive menu navigation
- **Secure authentication** with multiple protection layers
- **Search optimization** with domain extraction for better matches
- **Back navigation** throughout the application

## Installation

1. Clone the repository:
   ```
   https://github.com/TheKingHippopotamus/Secure_Password_Manager.git
   cd password-manager
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the password manager:
   ```
   python -m password_manager
   ```
   or
   ```
   ./run.py
   ```

## Usage

### First-time Setup
On first run, you'll be guided through creating a master account:
1. Enter a master username (minimum 4 characters)
2. Create a strong master password (minimum 8 characters)
3. Confirm your master password

This master account will be used to encrypt and decrypt all your stored passwords.

### Main Menu
The interactive menu provides access to all functionality:
```
=== Password Manager ===
Logged in as: your_username
1. Generate a new password
2. Save a password
3. Find passwords
4. List all websites
5. Delete a password
6. Create backup
7. Show storage location
8. Logout
9. Exit
```

### Managing Passwords
- **Generate passwords** with customizable length and character sets
- **Save passwords** for different websites/services with username and optional notes
- **Find passwords** by searching for website or username
- **View all websites** stored in the system
- **Delete passwords** with confirmation and re-authentication

## Security Architecture

The application implements multiple layers of security:

### Key Derivation
1. Your master password is never stored in its original form
2. A unique salt is generated for each master account
3. Password-Based Key Derivation Function 2 (PBKDF2) with 100,000 iterations is used
4. SHA-256 is used as the hashing algorithm

### Encryption Levels
1. **Machine-specific system key**: Derived from hardware identifiers and salt
   - Used to encrypt master username and password hash
   - Ties encrypted data to your specific device
   
2. **User-specific encryption key**: Derived from username, password, and salt
   - Used to encrypt/decrypt your password database
   - Requires both username and password to reconstruct

### Authentication Security
1. **Brute force protection**:
   - Limited login attempts (adaptive based on previous failures)
   - Device lockout after exceeded attempts
   - Increased security with each failed attempt
   
2. **Session security**:
   - Automatic timeout after 30 minutes of inactivity
   - Sensitive operations require re-authentication
   - Activity tracking to prevent session hijacking

### Data Security
1. **Filesystem security**:
   - Sensitive files stored in restricted permission directory (`mode 0o700`)
   - Files are hidden from casual directory listings
   - Naming convention prevents accidental exposure
   
2. **Data integrity**:
   - Backups are encrypted with the same security as the main database
   - File operations use safe write patterns to prevent corruption

## Directory Structure

```
~/.password_manager/
├── password_manager.log    # Application log (non-sensitive information)
├── backups/                # Encrypted backup storage directory
│   └── .passwords_backup_[timestamp].enc  # Encrypted backups
└── secrets/               # Directory for sensitive files (restricted permissions)
    ├── .passwords.enc     # Encrypted password database
    ├── salt.bin           # Salt for key derivation
    ├── .master_user.enc   # Encrypted master username
    ├── .master_hash.enc   # Encrypted master password hash
    └── .login_attempts.dat # Login attempt tracking for lockout system
```

The package itself follows a modular architecture:
```
password_manager/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point
├── manager.py           # Main SecurePasswordManager class
├── auth.py              # Authentication and master account management
├── encryption.py        # Encryption utilities
├── session.py           # Session management and timeout control
├── storage.py           # File storage operations
├── generator.py         # Password generation
├── utils.py             # Utility functions
├── logger.py            # Logging setup
└── constants.py         # Constants and configuration
```

## Advanced Usage

### Custom Password Generation
When generating passwords, you can specify:
- Password length (recommended 15+ characters)
- Whether to include special characters
- Whether to include uppercase letters
- Whether to include digits

Example of a highly secure password configuration:
- Length: 20+ characters
- Include all character types
- Resulting in an "Excellent" password strength rating

### Managing Sensitive Accounts
For highly sensitive accounts, consider:
1. Generating longer passwords (25+ characters)
2. Adding detailed notes about account recovery options
3. Creating regular backups after adding or updating important passwords

### Manual Backups
While automatic backups are created when using the backup feature, you can also manually copy the `.passwords.enc` file to a secure location for additional protection.

### Multi-Device Usage
This password manager is designed for single-device use with machine-specific encryption. For multi-device scenarios:
1. Install the password manager on each device
2. Create separate master accounts on each device
3. Use the built-in password generation on your primary device
4. Manually transfer passwords to secondary devices

## Security Best Practices

1. **Master Password Guidelines**:
   - Use a unique, strong master password (15+ characters)
   - Include a mix of character types
   - Avoid dictionary words and personal information
   - Consider using a passphrase of 4-5 random words

2. **Application Usage**:
   - Always log out when leaving your computer
   - Regularly create backups
   - Periodically review and update weak passwords
   - Do not run the application in untrusted environments

3. **System Security**:
   - Keep your operating system and Python updated
   - Use disk encryption on your computer
   - Protect your user account with a strong password
   - Consider using a firewall and antivirus protection

## Technical Details

### Cryptographic Implementation
- **Symmetric Encryption**: AES-256 in CBC mode with PKCS7 padding (via Fernet)
- **Key Derivation**: PBKDF2HMAC with SHA-256
- **Password Hashing**: SHA-256 with unique salt
- **Random Number Generation**: Cryptographically secure sources combined with time-based entropy

### Password Strength Evaluation
Passwords are evaluated based on:
- Length (30 points for 16+ characters)
- Character diversity (up to 60 points)
- Special characters (20 points)
- Uppercase letters (15 points)
- Digits (15 points)

Resulting in ratings:
- 80+ points: Excellent
- 60-79 points: Very Strong
- 40-59 points: Strong
- 25-39 points: Medium
- Below 25: Weak

### Lockout Mechanism
The adaptive lockout system:
1. Tracks login attempts per device
2. Reduces allowed attempts based on previous lockouts
3. Implements progressive security with repeated failures
4. Stores device identifiers and lockout information

## Requirements

- Python 3.6+
- cryptography library (for encryption)
- Operating system: Windows, macOS, or Linux
- Approximately 5MB of disk space

## License

GNU General Public License v3.0 (GPL-3.0)

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

Key requirements of this license:
- **Attribution**: You must give appropriate credit to the original author
- **Share Source Code**: If you distribute this software, you must make your source code available
- **Same License**: Any derivative works must be distributed under the same license
- **State Changes**: You must indicate any changes made to the original code

---

© 2023 Secure Password Manager. All rights reserved.  
@King.Hippopotamus

## Screenshots and Demo

### Application Interface
![Login Screen](static/Screenshot%202025-04-17%20at%2011.44.00.png)
*Login screen with secure authentication*

![Password Manager Dashboard](static/Screenshot%202025-04-17%20at%2011.48.49.png)
*Main dashboard interface showing stored passwords*

![Password Details](static/Screenshot%202025-04-17%20at%2011.51.02.png)
*Detailed view of password information*

### Video Demonstration
[![Watch the demo video](https://img.youtube.com/vi/9hPm1w-NM2Q/0.jpg)](https://youtu.be/9hPm1w-NM2Q)
*Click on the image above to watch the Password Manager demonstration video on YouTube*







# Secure_Password_Manager
