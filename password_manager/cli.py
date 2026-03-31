#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
IronDome CLI entry points.

Two commands are exposed via pyproject.toml [project.scripts]:

    irondome — system-level operations (init, open/close airspace, status)
    bunker   — vault (password entry) operations

Both commands share the same `~/.password_manager` data directory and
coordinate through the Airspace session file so that
`irondome open airspace` followed by `bunker open -o github` works
across separate processes without re-prompting for credentials.
"""

import argparse
import os
import sys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _data_dir() -> str:
    """Canonical data directory — identical to the one used by SecurePasswordManager."""
    return os.path.join(os.path.expanduser("~"), ".password_manager")


def _build_manager_components(data_dir: str):
    """
    Construct the minimal set of low-level objects needed by CLI sub-commands
    that do NOT want the full SecurePasswordManager initialisation flow
    (which prompts for credentials on its own).

    Returns a tuple: (storage, session, auth, logger)
    """
    from password_manager.storage import PasswordStorage
    from password_manager.session import SessionManager
    from password_manager.auth import AuthManager
    from password_manager.logger import setup_logger

    log_file = os.path.join(data_dir, "password_manager.log")
    logger = setup_logger(log_file)
    storage = PasswordStorage(data_dir, logger)
    session = SessionManager(storage.login_attempts_file, logger)
    auth = AuthManager(storage, session, logger)
    return storage, session, auth, logger


# ---------------------------------------------------------------------------
# irondome entry point
# ---------------------------------------------------------------------------

def irondome_main() -> None:
    """Entry point for the `irondome` command."""
    parser = argparse.ArgumentParser(
        prog="irondome",
        description="IronDome — Secure CLI Password Vault",
    )
    subparsers = parser.add_subparsers(dest="command")

    # irondome create bunker — first-time vault initialisation
    create_parser = subparsers.add_parser("create", help="Create and configure")
    create_parser.add_argument(
        "target",
        choices=["bunker"],
        help="What to create",
    )

    # irondome open airspace — authenticate and open session
    open_parser = subparsers.add_parser("open", help="Open access")
    open_parser.add_argument(
        "target",
        choices=["airspace"],
        help="What to open",
    )

    # irondome close airspace — lock everything
    close_parser = subparsers.add_parser("close", help="Close access")
    close_parser.add_argument(
        "target",
        choices=["airspace"],
        help="What to close",
    )

    # irondome status
    subparsers.add_parser("status", help="Show IronDome status")

    args = parser.parse_args()

    data_dir = _data_dir()

    from password_manager.airspace import Airspace
    from password_manager.settings import Settings
    from password_manager.biometric import BiometricAuth

    airspace = Airspace(data_dir)

    # ------------------------------------------------------------------
    # No sub-command — fall through to interactive mode
    # ------------------------------------------------------------------
    if args.command is None:
        from password_manager.manager import SecurePasswordManager
        manager = SecurePasswordManager()
        if manager.session.session_authenticated:
            manager.run_interactive_menu()
        return

    # ------------------------------------------------------------------
    # irondome create bunker
    # ------------------------------------------------------------------
    if args.command == "create" and args.target == "bunker":
        from password_manager.storage import PasswordStorage

        os.makedirs(data_dir, exist_ok=True)
        storage = PasswordStorage(data_dir)

        if storage.master_account_exists():
            print(
                "IronDome is already configured. "
                "Use 'irondome open airspace' to unlock."
            )
            return

        print("=== IronDome — First Time Setup ===")
        _, _, auth, _ = _build_manager_components(data_dir)

        result = auth.setup_security_mode()
        if result:
            settings = Settings(data_dir)
            print("\nConfigure your defaults:")
            settings.run_interactive()
            print(
                "\nIronDome configured. "
                "Use 'irondome open airspace' to start."
            )
        return

    # ------------------------------------------------------------------
    # irondome open airspace
    # ------------------------------------------------------------------
    if args.command == "open" and args.target == "airspace":
        if airspace.is_open():
            print(
                f"Airspace already open. "
                f"{airspace.remaining_minutes()} minutes remaining."
            )
            return

        from password_manager.storage import PasswordStorage

        storage = PasswordStorage(data_dir)
        if not storage.master_account_exists():
            print("No dome configured. Run 'irondome create bunker' first.")
            return

        _, _, auth, _ = _build_manager_components(data_dir)
        settings = Settings(data_dir)
        timeout = settings.get("session_timeout", 1800)

        print("Opening airspace...")
        result = auth.authenticate_biometric()
        if result:
            airspace.open(timeout=timeout)
            mins = timeout // 60
            print(f"Airspace open. You have {mins} minutes of free access.")
            print("   Run 'bunker' commands freely.")
            print("   Run 'irondome close airspace' to lock down.")
        else:
            print("Authentication failed. Airspace remains closed.")
        return

    # ------------------------------------------------------------------
    # irondome close airspace
    # ------------------------------------------------------------------
    if args.command == "close" and args.target == "airspace":
        airspace.close()
        print("Airspace closed. All access locked.")
        return

    # ------------------------------------------------------------------
    # irondome status
    # ------------------------------------------------------------------
    if args.command == "status":
        _print_status(data_dir, airspace)
        return


# ---------------------------------------------------------------------------
# bunker entry point
# ---------------------------------------------------------------------------

def bunker_main() -> None:
    """Entry point for the `bunker` command."""
    parser = argparse.ArgumentParser(
        prog="bunker",
        description="IronDome bunker operations",
    )
    subparsers = parser.add_subparsers(dest="command")

    # bunker create / bunker -c — quick-create a password entry
    subparsers.add_parser("create", help="Quick-create a bunker entry")
    subparsers.add_parser("-c", help=argparse.SUPPRESS)

    # bunker open / bunker -o [name] — open/list bunkers
    open_parser = subparsers.add_parser("open", help="Open/list bunkers")
    open_parser.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Bunker name to open",
    )
    open_alias = subparsers.add_parser("-o", help=argparse.SUPPRESS)
    open_alias.add_argument("name", nargs="?", default=None)

    # bunker fortify — create encrypted backup
    subparsers.add_parser("fortify", help="Create encrypted backup")

    # bunker settings — configure defaults
    subparsers.add_parser("settings", help="Configure defaults")

    # bunker status — show dome info
    subparsers.add_parser("status", help="Show dome info")

    args = parser.parse_args()

    data_dir = _data_dir()

    from password_manager.airspace import Airspace
    from password_manager.settings import Settings

    airspace = Airspace(data_dir)

    # ------------------------------------------------------------------
    # No sub-command — interactive mode (authenticates on its own)
    # ------------------------------------------------------------------
    if args.command is None:
        from password_manager.manager import SecurePasswordManager
        manager = SecurePasswordManager()
        if manager.session.session_authenticated:
            manager.run_interactive_menu()
        return

    # ------------------------------------------------------------------
    # bunker settings — no airspace required
    # ------------------------------------------------------------------
    if args.command == "settings":
        settings = Settings(data_dir)
        settings.run_interactive()
        return

    # ------------------------------------------------------------------
    # bunker status — delegate to irondome status logic
    # ------------------------------------------------------------------
    if args.command == "status":
        _print_status(data_dir, airspace)
        return

    # ------------------------------------------------------------------
    # All remaining sub-commands require open airspace
    # ------------------------------------------------------------------
    if not airspace.is_open():
        print("Airspace is closed. Run 'irondome open airspace' first.")
        sys.exit(1)

    # Initialise manager — airspace is already open so SecurePasswordManager
    # will find the session and skip interactive authentication prompts only
    # when the underlying SessionManager detects an active session.
    # If auth still fails (e.g. session file present but keys differ) we abort.
    from password_manager.manager import SecurePasswordManager
    manager = SecurePasswordManager()

    if not manager.session.session_authenticated:
        print("Authentication failed.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # bunker create / -c
    # ------------------------------------------------------------------
    if args.command in ("create", "-c"):
        settings = Settings(data_dir)

        pwd_info = manager.generate_password(
            length=settings.get("password_length", 20),
            use_special=settings.get("use_special_chars", True),
            use_uppercase=settings.get("use_uppercase", True),
            use_digits=settings.get("use_digits", True),
        )

        if not pwd_info:
            return

        print(f"\nGenerated: {pwd_info['password']}")
        if settings.get("show_strength", True):
            print(f"Strength: {pwd_info['strength']}")

        username = input("\nUsername: ").strip()
        if not username:
            print("Bunker not saved.")
            return

        website = input("Service/site: ").strip()
        if not website:
            print("Bunker not saved.")
            return

        notes = input("Notes (optional): ").strip()

        manager.save_password(username, website, pwd_info["password"], notes)
        return

    # ------------------------------------------------------------------
    # bunker open / -o [name]
    # ------------------------------------------------------------------
    if args.command in ("open", "-o"):
        name = getattr(args, "name", None)
        if name:
            results = manager.find_password(name)
            if results:
                for entry in results:
                    print(f"\n  Service:  {entry['website']}")
                    print(f"  Username: {entry['username']}")
                    print(f"  Password: {entry['password']}")
                    if entry.get("notes"):
                        print(f"  Notes:    {entry['notes']}")
                    print(f"  Created:  {entry['created_at']}")
            else:
                print(f"No bunker found matching '{name}'")
        else:
            websites = manager.list_websites()
            if websites:
                print("\n=== Bunker Registry ===")
                for idx, site in enumerate(websites, 1):
                    print(f"  {idx}. {site}")
                print(f"\n  Total: {len(websites)} bunkers")
            else:
                print("No bunkers stored.")
        return

    # ------------------------------------------------------------------
    # bunker fortify
    # ------------------------------------------------------------------
    if args.command == "fortify":
        result = manager.backup_passwords()
        if result:
            print("Dome fortified. Backup created.")
        return


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _print_status(data_dir: str, airspace) -> None:
    """Print a unified IronDome status block."""
    from password_manager.storage import PasswordStorage
    from password_manager.settings import Settings
    from password_manager.biometric import BiometricAuth

    storage = PasswordStorage(data_dir)
    configured = storage.master_account_exists()

    print("=== IronDome Status ===")
    print(f"  Dome:     {'configured' if configured else 'not configured'}")

    if airspace.is_open():
        print(f"  Airspace: OPEN - {airspace.remaining_minutes()} min remaining")
    else:
        print("  Airspace: CLOSED")

    if configured:
        settings = Settings(data_dir)
        bio = BiometricAuth()
        bio_type = bio.get_type()
        print(f"  Biometric: {bio_type if bio_type else 'not available'}")
        print(f"  Timeout:  {settings.get('session_timeout', 1800) // 60} min")

        info = storage.get_storage_info()
        if "password_file_size" in info:
            print(f"  Vault:    {info['password_file_size']} bytes")
