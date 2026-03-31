#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Biometric authentication module for IronDome password manager.

Provides cross-platform biometric authentication via:
  - macOS: Touch ID (LocalAuthentication framework via Swift subprocess or pyobjc)
  - Windows: Windows Hello (UserConsentVerifier via PowerShell)
  - Linux: Fingerprint via fprintd

Security guarantees:
  - No credentials are stored or transmitted by this module
  - All subprocess calls use capture_output=True (no terminal leaks)
  - All blocking calls time out after 30 seconds
  - Biometric data is never logged
  - All failures return False gracefully — this module never raises to callers
"""

import platform
import shutil
import subprocess
import logging
from typing import Optional


# Availability result cache sentinel — distinguishes "not yet checked" from False
_NOT_CHECKED = object()

# Timeout in seconds for any blocking biometric prompt
_BIOMETRIC_TIMEOUT = 30


class BiometricAuth:
    """
    Cross-platform biometric authentication.

    Usage:
        bio = BiometricAuth(logger=my_logger)
        if bio.is_available():
            success = bio.authenticate("IronDome vault access")
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize the biometric authenticator.

        Args:
            logger: Optional Logger instance. If None, a no-op logger is used.
                    Biometric data is never written to the log.
        """
        self.logger: logging.Logger = logger or logging.getLogger(__name__)
        self._platform: str = platform.system()  # "Darwin", "Windows", "Linux"
        self._available: object = _NOT_CHECKED   # cached after first is_available() call
        self._type: Optional[str] = None         # cached biometric type string

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """
        Return True if the current platform has biometric hardware with enrolled
        biometrics. Results are cached after the first call.

        This method is non-blocking and issues no authentication prompts.
        """
        if self._available is not _NOT_CHECKED:
            return bool(self._available)

        try:
            if self._platform == "Darwin":
                result = self._check_macos()
            elif self._platform == "Windows":
                result = self._check_windows()
            elif self._platform == "Linux":
                result = self._check_linux()
            else:
                self.logger.info(
                    "BiometricAuth: unsupported platform '%s'", self._platform
                )
                result = False
        except Exception:
            self.logger.exception("BiometricAuth: unexpected error during availability check")
            result = False

        self._available = result
        return result

    def get_type(self) -> str:
        """
        Return a human-readable biometric type name.

        Returns one of: "Touch ID", "Windows Hello", "Fingerprint", "None"
        """
        if self._type is not None:
            return self._type

        if not self.is_available():
            self._type = "None"
            return self._type

        if self._platform == "Darwin":
            self._type = "Touch ID"
        elif self._platform == "Windows":
            self._type = "Windows Hello"
        elif self._platform == "Linux":
            self._type = "Fingerprint"
        else:
            self._type = "None"

        return self._type

    def authenticate(self, reason: str = "IronDome vault access") -> bool:
        """
        Prompt the user for biometric authentication.

        Args:
            reason: Human-readable reason shown to the user in the biometric
                    prompt (macOS and Windows surfaces this to the OS UI).

        Returns:
            True if the user successfully authenticated, False for any
            failure including hardware errors, timeouts, user cancellation,
            or biometric not being available.
        """
        if not self.is_available():
            self.logger.info("BiometricAuth: authentication skipped — biometrics not available")
            return False

        self.logger.info("BiometricAuth: authentication attempt started (platform=%s)", self._platform)

        try:
            if self._platform == "Darwin":
                result = self._auth_macos(reason)
            elif self._platform == "Windows":
                result = self._auth_windows(reason)
            elif self._platform == "Linux":
                result = self._auth_linux(reason)
            else:
                result = False
        except Exception:
            self.logger.exception("BiometricAuth: unexpected error during authentication")
            result = False

        # Log outcome without any biometric data
        if result:
            self.logger.info("BiometricAuth: authentication succeeded")
        else:
            self.logger.warning("BiometricAuth: authentication failed or was cancelled")

        return result

    # ------------------------------------------------------------------
    # Private — macOS (Touch ID / LocalAuthentication)
    # ------------------------------------------------------------------

    def _check_macos(self) -> bool:
        """
        Check Touch ID availability on macOS.

        Prefers pyobjc-framework-LocalAuthentication when installed.
        Falls back to a Swift subprocess one-liner.
        """
        # --- Attempt 1: pyobjc (no extra process spawn needed) ---
        try:
            import objc  # noqa: F401 — availability probe only
            from LocalAuthentication import LAContext, LAPolicyDeviceOwnerAuthenticationWithBiometrics
            context = LAContext.new()
            error_ptr = None
            can_evaluate = context.canEvaluatePolicy_error_(
                LAPolicyDeviceOwnerAuthenticationWithBiometrics,
                error_ptr
            )
            if can_evaluate:
                self.logger.info("BiometricAuth: Touch ID available (pyobjc path)")
                return True
            self.logger.info("BiometricAuth: Touch ID not available via pyobjc")
            return False
        except ImportError:
            pass  # pyobjc not installed — fall through to Swift
        except Exception:
            self.logger.exception("BiometricAuth: pyobjc check raised unexpectedly")
            # Fall through to Swift

        # --- Attempt 2: Swift subprocess ---
        return self._macos_swift_check()

    def _macos_swift_check(self) -> bool:
        """
        Use a Swift one-liner to test LAContext biometric availability.
        """
        if not shutil.which("swift"):
            self.logger.info("BiometricAuth: 'swift' not found in PATH — Touch ID check unavailable")
            return False

        swift_code = (
            "import LocalAuthentication; import Foundation; "
            "let ctx = LAContext(); var err: NSError?; "
            "let ok = ctx.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &err); "
            "print(ok ? \"YES\" : \"NO\"); exit(ok ? 0 : 1)"
        )

        try:
            result = subprocess.run(
                ["swift", "-e", swift_code],
                capture_output=True,
                text=True,
                timeout=_BIOMETRIC_TIMEOUT,
            )
            available = result.returncode == 0 and "YES" in result.stdout
            self.logger.info(
                "BiometricAuth: Swift availability check returncode=%d available=%s",
                result.returncode,
                available,
            )
            return available
        except subprocess.TimeoutExpired:
            self.logger.warning("BiometricAuth: Swift availability check timed out")
            return False
        except Exception:
            self.logger.exception("BiometricAuth: Swift availability check failed")
            return False

    def _auth_macos(self, reason: str) -> bool:
        """
        Authenticate with Touch ID on macOS.

        Prefers pyobjc when installed. Falls back to Swift subprocess.
        """
        # --- Attempt 1: pyobjc ---
        try:
            import objc  # noqa: F401
            from LocalAuthentication import (
                LAContext,
                LAPolicyDeviceOwnerAuthenticationWithBiometrics,
            )
            import threading

            context = LAContext.new()
            event = threading.Event()
            result_holder: list = [False]

            def handler(success, error):
                result_holder[0] = bool(success)
                event.set()

            context.evaluatePolicy_localizedReason_reply_(
                LAPolicyDeviceOwnerAuthenticationWithBiometrics,
                reason,
                handler,
            )

            signalled = event.wait(timeout=_BIOMETRIC_TIMEOUT)
            if not signalled:
                self.logger.warning("BiometricAuth: pyobjc authentication timed out")
                return False

            return result_holder[0]

        except ImportError:
            pass  # fall through to Swift
        except Exception:
            self.logger.exception("BiometricAuth: pyobjc authentication raised unexpectedly")
            # Fall through to Swift

        # --- Attempt 2: Swift subprocess ---
        return self._macos_swift_auth(reason)

    def _macos_swift_auth(self, reason: str) -> bool:
        """
        Authenticate via Touch ID using a Swift subprocess one-liner.

        The Swift code calls LAContext.evaluatePolicy synchronously via a
        DispatchSemaphore, which is safe for a short-lived subprocess.
        """
        if not shutil.which("swift"):
            self.logger.info("BiometricAuth: 'swift' not found in PATH — cannot authenticate")
            return False

        # Sanitise the reason string to prevent Swift string-literal injection.
        # The reason is embedded inside a Swift string literal delimited by
        # double-quotes.  Strip every character that could escape that literal
        # or introduce new statements: double-quotes, backslashes, backticks,
        # newlines, carriage returns, and null bytes.
        _SWIFT_REASON_UNSAFE = str.maketrans("", "", '"\\\n\r\x00`')
        safe_reason = reason.translate(_SWIFT_REASON_UNSAFE)[:128]

        swift_code = f"""
import LocalAuthentication
import Foundation
let context = LAContext()
var error: NSError?
guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {{
    print("NO_BIOMETRIC")
    exit(1)
}}
let semaphore = DispatchSemaphore(value: 0)
var success = false
context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, localizedReason: "{safe_reason}") {{ result, _ in
    success = result
    semaphore.signal()
}}
semaphore.wait()
print(success ? "OK" : "FAIL")
exit(success ? 0 : 1)
"""

        try:
            result = subprocess.run(
                ["swift", "-e", swift_code],
                capture_output=True,
                text=True,
                timeout=_BIOMETRIC_TIMEOUT,
            )
            stdout = result.stdout.strip()
            self.logger.info(
                "BiometricAuth: Swift auth returncode=%d stdout=%s",
                result.returncode,
                stdout,
            )
            return result.returncode == 0 and stdout == "OK"
        except subprocess.TimeoutExpired:
            self.logger.warning("BiometricAuth: Swift authentication timed out after %ds", _BIOMETRIC_TIMEOUT)
            return False
        except Exception:
            self.logger.exception("BiometricAuth: Swift authentication subprocess failed")
            return False

    # ------------------------------------------------------------------
    # Private — Windows (Windows Hello)
    # ------------------------------------------------------------------

    def _check_windows(self) -> bool:
        """
        Check Windows Hello availability.

        Queries the TPM via WMI and verifies the UserConsentVerifier API
        is accessible. Both checks must pass for True to be returned.
        """
        # Check TPM presence (required by Windows Hello)
        tpm_available = self._windows_tpm_check()
        if not tpm_available:
            self.logger.info("BiometricAuth: Windows Hello unavailable — TPM not found or not ready")
            return False

        # Verify Windows.Security.Credentials.UI namespace is usable
        ps_check = (
            "Add-Type -AssemblyName Windows.Security; "
            "$t = [Windows.Security.Credentials.UI.UserConsentVerifier]; "
            "Write-Output 'OK'"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NonInteractive", "-Command", ps_check],
                capture_output=True,
                text=True,
                timeout=10,
            )
            available = result.returncode == 0 and "OK" in result.stdout
            self.logger.info(
                "BiometricAuth: Windows Hello availability check returncode=%d",
                result.returncode,
            )
            return available
        except subprocess.TimeoutExpired:
            self.logger.warning("BiometricAuth: Windows Hello availability check timed out")
            return False
        except FileNotFoundError:
            self.logger.info("BiometricAuth: PowerShell not found — Windows Hello check unavailable")
            return False
        except Exception:
            self.logger.exception("BiometricAuth: Windows Hello availability check failed")
            return False

    def _windows_tpm_check(self) -> bool:
        """
        Query WMI for a present and enabled TPM chip — a prerequisite for
        Windows Hello biometrics.
        """
        ps_tpm = (
            "try { "
            "$tpm = Get-WmiObject -Namespace root/cimv2/security/microsofttpm "
            "-Class Win32_Tpm -ErrorAction Stop; "
            "if ($tpm -and $tpm.IsEnabled_InitialValue) { Write-Output 'TPM_OK' } "
            "else { Write-Output 'TPM_DISABLED' } "
            "} catch { Write-Output 'TPM_MISSING' }"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NonInteractive", "-Command", ps_tpm],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return "TPM_OK" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False

    def _auth_windows(self, reason: str) -> bool:
        """
        Authenticate via Windows Hello using the UserConsentVerifier API.

        Invokes a PowerShell script that calls the WinRT
        UserConsentVerifier.RequestVerificationAsync method synchronously
        via GetAwaiter().GetResult().
        """
        # Sanitise reason to prevent PowerShell injection.
        # The reason is interpolated inside a PowerShell double-quoted string.
        # Strip every character that PowerShell treats as a special/escape
        # sequence inside such strings: double-quotes, backticks (PS escape
        # char), dollar signs (variable expansion), newlines, carriage returns,
        # null bytes, semicolons (statement separators), and parentheses
        # (sub-expression syntax). Enforce a length cap of 128 characters.
        _PS_REASON_UNSAFE = str.maketrans("", "", '"\'`$\n\r\x00;()')
        safe_reason = reason.translate(_PS_REASON_UNSAFE)[:128]

        ps_script = (
            "Add-Type -AssemblyName Windows.Security; "
            "$verifier = [Windows.Security.Credentials.UI.UserConsentVerifier]; "
            '$result = $verifier::RequestVerificationAsync("{reason}").GetAwaiter().GetResult(); '
            "$verified = [Windows.Security.Credentials.UI.UserConsentVerificationResult]::Verified; "
            "if ($result -eq $verified) {{ exit 0 }} else {{ exit 1 }}"
        ).format(reason=safe_reason)

        try:
            result = subprocess.run(
                ["powershell", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=_BIOMETRIC_TIMEOUT,
            )
            self.logger.info(
                "BiometricAuth: Windows Hello auth returncode=%d",
                result.returncode,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            self.logger.warning("BiometricAuth: Windows Hello authentication timed out after %ds", _BIOMETRIC_TIMEOUT)
            return False
        except FileNotFoundError:
            self.logger.info("BiometricAuth: PowerShell not found — Windows Hello authentication unavailable")
            return False
        except Exception:
            self.logger.exception("BiometricAuth: Windows Hello authentication failed")
            return False

    # ------------------------------------------------------------------
    # Private — Linux (fprintd)
    # ------------------------------------------------------------------

    def _check_linux(self) -> bool:
        """
        Check fingerprint availability on Linux via fprintd.

        Requires:
          - fprintd-verify in PATH
          - fprintd-list in PATH (to confirm enrolled fingerprints)
        """
        if not shutil.which("fprintd-verify"):
            self.logger.info("BiometricAuth: 'fprintd-verify' not found in PATH")
            return False

        if not shutil.which("fprintd-list"):
            # fprintd-verify is present but we cannot confirm enrollment
            self.logger.info(
                "BiometricAuth: 'fprintd-list' not found — cannot confirm enrolled fingerprints"
            )
            return False

        # Check whether any fingerprints are enrolled for the current user
        import os
        current_user = os.environ.get("USER") or os.environ.get("LOGNAME") or ""

        try:
            result = subprocess.run(
                ["fprintd-list", current_user],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # fprintd-list exits 0 and prints enrolled fingers when biometrics exist;
            # it prints "no fingers enrolled" or similar on failure
            enrolled = (
                result.returncode == 0
                and "no fingers" not in result.stdout.lower()
                and result.stdout.strip() != ""
            )
            self.logger.info(
                "BiometricAuth: fprintd-list returncode=%d enrolled=%s",
                result.returncode,
                enrolled,
            )
            return enrolled
        except subprocess.TimeoutExpired:
            self.logger.warning("BiometricAuth: fprintd-list timed out")
            return False
        except Exception:
            self.logger.exception("BiometricAuth: fprintd-list check failed")
            return False

    def _auth_linux(self, reason: str) -> bool:
        """
        Authenticate via fingerprint on Linux using fprintd-verify.

        Note: fprintd-verify does not accept a custom reason string — the
        reason parameter is accepted for API consistency but is not forwarded
        to the subprocess.
        """
        if not shutil.which("fprintd-verify"):
            self.logger.info("BiometricAuth: 'fprintd-verify' not found — cannot authenticate")
            return False

        try:
            result = subprocess.run(
                ["fprintd-verify"],
                capture_output=True,
                text=True,
                timeout=_BIOMETRIC_TIMEOUT,
            )
            self.logger.info(
                "BiometricAuth: fprintd-verify returncode=%d",
                result.returncode,
            )
            # fprintd-verify exits 0 on successful verification
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            self.logger.warning("BiometricAuth: fprintd-verify timed out after %ds", _BIOMETRIC_TIMEOUT)
            return False
        except Exception:
            self.logger.exception("BiometricAuth: fprintd-verify authentication failed")
            return False
