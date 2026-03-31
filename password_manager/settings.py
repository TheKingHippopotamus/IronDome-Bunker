#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Settings management for IronDome"""

import json
import os
from typing import Any, Optional

DEFAULTS = {
    "password_length": 20,
    "use_special_chars": True,
    "use_uppercase": True,
    "use_digits": True,
    "session_timeout": 1800,  # 30 minutes
    "auto_copy_clipboard": False,
    "show_strength": True,
}


class Settings:
    """Manages IronDome user preferences"""

    def __init__(self, data_dir: str):
        self.config_path = os.path.join(data_dir, "settings.json")
        self._settings = dict(DEFAULTS)
        self.load()

    def load(self) -> None:
        """Load settings from disk, merge with defaults"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    saved = json.load(f)
                # Merge — saved values override defaults, unknown keys ignored
                for key in DEFAULTS:
                    if key in saved:
                        self._settings[key] = saved[key]
            except (json.JSONDecodeError, IOError):
                pass  # Use defaults on corrupt file

    def save(self) -> bool:
        """Save current settings to disk"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self._settings, f, indent=2)
            return True
        except IOError:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if key in DEFAULTS:
            self._settings[key] = value
            self.save()

    def get_all(self) -> dict:
        return dict(self._settings)

    def reset(self) -> None:
        """Reset all settings to defaults"""
        self._settings = dict(DEFAULTS)
        self.save()

    def run_interactive(self) -> None:
        """Interactive settings menu"""
        while True:
            print("\n=== IronDome Settings ===")
            print(f"  1. Password length:    {self.get('password_length')}")
            print(f"  2. Special characters: {'yes' if self.get('use_special_chars') else 'no'}")
            print(f"  3. Uppercase letters:  {'yes' if self.get('use_uppercase') else 'no'}")
            print(f"  4. Include digits:     {'yes' if self.get('use_digits') else 'no'}")
            print(f"  5. Session timeout:    {self.get('session_timeout') // 60} min")
            print(f"  6. Show strength:      {'yes' if self.get('show_strength') else 'no'}")
            print(f"  7. Reset to defaults")
            print(f"  8. Back")

            choice = input("\nSelect (1-8): ").strip()

            if choice == '1':
                val = input(f"Password length (current: {self.get('password_length')}): ").strip()
                try:
                    length = int(val)
                    if 4 <= length <= 200:
                        self.set('password_length', length)
                        print(f"Password length set to {length}")
                    else:
                        print("Must be between 4 and 200")
                except ValueError:
                    print("Invalid number")
            elif choice == '2':
                current = self.get('use_special_chars')
                self.set('use_special_chars', not current)
                print(f"Special characters: {'yes' if not current else 'no'}")
            elif choice == '3':
                current = self.get('use_uppercase')
                self.set('use_uppercase', not current)
                print(f"Uppercase letters: {'yes' if not current else 'no'}")
            elif choice == '4':
                current = self.get('use_digits')
                self.set('use_digits', not current)
                print(f"Digits: {'yes' if not current else 'no'}")
            elif choice == '5':
                val = input(f"Session timeout in minutes (current: {self.get('session_timeout') // 60}): ").strip()
                try:
                    minutes = int(val)
                    if 1 <= minutes <= 480:
                        self.set('session_timeout', minutes * 60)
                        print(f"Session timeout set to {minutes} min")
                    else:
                        print("Must be between 1 and 480 minutes")
                except ValueError:
                    print("Invalid number")
            elif choice == '6':
                current = self.get('show_strength')
                self.set('show_strength', not current)
                print(f"Show strength: {'yes' if not current else 'no'}")
            elif choice == '7':
                self.reset()
                print("Settings reset to defaults")
            elif choice == '8':
                break
