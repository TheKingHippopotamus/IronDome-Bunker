#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Airspace session management for IronDome.

The "airspace" is the concept of an open authentication session.  When
airspace is open, the user has already proven identity and commands run
without re-prompting.  When closed (expired or manually locked), every
operation that touches vault data is blocked.

Session state is persisted to a JSON file under the secrets directory so
it survives across sub-process calls (e.g. `bunker open -o` after
`irondome open airspace`).
"""

import json
import os
import time


class Airspace:
    """Manages the IronDome airspace session — open = authenticated, closed = locked."""

    def __init__(self, data_dir: str):
        self.session_file = os.path.join(data_dir, "secrets", ".airspace.session")
        self.timeout = 1800  # 30 minutes default

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_open(self) -> bool:
        """Return True if a valid, non-expired session exists."""
        if not os.path.exists(self.session_file):
            return False
        try:
            with open(self.session_file, "r") as f:
                data = json.load(f)
            opened_at = data.get("opened_at", 0)
            timeout = data.get("timeout", self.timeout)
            if time.time() - opened_at > timeout:
                self.close()
                return False
            return True
        except (json.JSONDecodeError, IOError):
            return False

    def open(self, timeout: int = None) -> bool:
        """
        Create the session file, marking airspace as open.

        Args:
            timeout: Session lifetime in seconds (default: self.timeout).

        Returns:
            True on success, False if the file could not be written.
        """
        try:
            effective_timeout = timeout if timeout is not None else self.timeout
            data = {
                "opened_at": time.time(),
                "timeout": effective_timeout,
                "pid": os.getpid(),
            }
            os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
            with open(self.session_file, "w") as f:
                json.dump(data, f)
            os.chmod(self.session_file, 0o600)
            return True
        except IOError:
            return False

    def close(self) -> bool:
        """
        Delete the session file, locking the airspace.

        Returns:
            True on success (including when the file did not exist),
            False if deletion raised an IOError.
        """
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            return True
        except IOError:
            return False

    def remaining_minutes(self) -> int:
        """
        Return the number of whole minutes remaining in the current session.

        Returns 0 if airspace is closed or the file cannot be read.
        """
        if not os.path.exists(self.session_file):
            return 0
        try:
            with open(self.session_file, "r") as f:
                data = json.load(f)
            elapsed = time.time() - data.get("opened_at", 0)
            timeout = data.get("timeout", self.timeout)
            remaining = max(0.0, timeout - elapsed)
            return int(remaining / 60)
        except (json.JSONDecodeError, IOError):
            return 0

    def remaining_seconds(self) -> int:
        """
        Return the number of whole seconds remaining in the current session.

        Returns 0 if airspace is closed or the file cannot be read.
        """
        if not os.path.exists(self.session_file):
            return 0
        try:
            with open(self.session_file, "r") as f:
                data = json.load(f)
            elapsed = time.time() - data.get("opened_at", 0)
            timeout = data.get("timeout", self.timeout)
            return int(max(0.0, timeout - elapsed))
        except (json.JSONDecodeError, IOError):
            return 0

    def extend(self, extra_seconds: int = 1800) -> bool:
        """
        Push the expiry forward by resetting opened_at to now while keeping
        the configured timeout.  Useful for "keep-alive" touch operations.

        Args:
            extra_seconds: Not used directly; the session is simply
                refreshed from the current moment with the original timeout.

        Returns:
            True if the session was refreshed, False if it was already
            closed or if writing the file failed.
        """
        if not self.is_open():
            return False
        try:
            with open(self.session_file, "r") as f:
                data = json.load(f)
            data["opened_at"] = time.time()
            with open(self.session_file, "w") as f:
                json.dump(data, f)
            os.chmod(self.session_file, 0o600)
            return True
        except (json.JSONDecodeError, IOError):
            return False
