#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Secure Password Manager

This program allows you to:
1. Generate strong, random passwords
2. Store passwords securely (encrypted) in a local file
3. Retrieve passwords when needed
4. Search for passwords by username or website

All data is stored locally in encrypted form at ~/.password_manager/.passwords.enc
"""

from password_manager.manager import SecurePasswordManager

def main():
    """Run the password manager application"""
    print("=== Secure Password Manager ===")
    print("All data is stored locally and encrypted")
    
    manager = None
    try:
        manager = SecurePasswordManager()
        manager.run_interactive_menu()
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
        # Don't log the error details to console for security reasons
        if manager is not None and hasattr(manager, 'logger'):
            manager.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 