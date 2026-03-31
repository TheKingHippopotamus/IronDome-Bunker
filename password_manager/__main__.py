#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Secure Password Manager — module entry point.

Running `python -m password_manager` is equivalent to the `bunker` command.
This preserves backward compatibility for users who invoked the package
directly before the `bunker` / `irondome` CLI entry points were added.
"""

from password_manager.cli import bunker_main


def main() -> None:
    """Run the password manager application via the bunker CLI entry point."""
    bunker_main()


if __name__ == "__main__":
    main() 