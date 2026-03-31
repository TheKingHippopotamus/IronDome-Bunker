#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Session management for IronDome"""

import time
import json
import threading
from datetime import datetime, timedelta
from password_manager.utils import get_machine_info
from password_manager.constants import SESSION_TIMEOUT, MAX_LOGIN_ATTEMPTS, LOCKOUT_DURATION

class SessionManager:
    """Manages user sessions, timeout and authentication tracking"""
    
    def __init__(self, login_attempts_file, logger=None):
        """
        Initialize the session manager
        
        Args:
            login_attempts_file: Path to the login attempts tracking file
            logger: Optional logger instance
        """
        self.login_attempts_file = login_attempts_file
        self.logger = logger
        self.session_authenticated = False
        self.username = None
        self.last_activity_time = time.time()
        self.session_timeout = SESSION_TIMEOUT
        self.max_login_attempts = MAX_LOGIN_ATTEMPTS
        self.lockout_duration = LOCKOUT_DURATION
        
        # Start session timeout checker
        self.start_session_checker()
    
    def check_login_attempts(self):
        """
        Check if the current machine is allowed to attempt login
        
        Returns:
            Dictionary with login attempt status
        """
        machine_info = get_machine_info()
        machine_id = machine_info["mac_address"]
        
        # Load login attempts data
        login_data = self._load_login_attempts()
        
        # Check if machine is locked out
        if machine_id in login_data:
            machine_data = login_data[machine_id]
            
            # If lockout time exists and still valid
            if "lockout_until" in machine_data:
                lockout_time = datetime.strptime(machine_data["lockout_until"], "%Y-%m-%d %H:%M:%S")
                
                if datetime.now() < lockout_time:
                    # Still locked out
                    remaining = (lockout_time - datetime.now()).total_seconds() / 60
                    if self.logger:
                        self.logger.warning(f"Login blocked - device is locked out for {remaining:.1f} more minutes")
                    return {
                        "allowed": False,
                        "remaining_time": remaining,
                        "message": f"Login blocked. Try again in {remaining:.1f} minutes."
                    }
                else:
                    # Lockout expired, reset attempts but keep track of previous failures
                    machine_data["failed_attempts"] = 0
                    machine_data["previous_lockouts"] += 1
                    machine_data.pop("lockout_until", None)
                    login_data[machine_id] = machine_data
                    self._save_login_attempts(login_data)
        
        return {"allowed": True}
    
    def update_login_attempts(self, success):
        """
        Update the login attempts tracking after a login attempt
        
        Args:
            success: Whether login was successful
            
        Returns:
            Dictionary with updated login attempt info
        """
        machine_info = get_machine_info()
        machine_id = machine_info["mac_address"]
        
        # Load existing data
        login_data = self._load_login_attempts()
        
        # Get or create machine data
        if machine_id not in login_data:
            machine_data = {
                "machine_info": machine_info,
                "failed_attempts": 0,
                "previous_lockouts": 0,
                "last_attempt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            machine_data = login_data[machine_id]
            machine_data["last_attempt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            machine_data["machine_info"] = machine_info  # Update machine info
        
        # Update based on success/failure
        if success:
            # Reset failed attempts on success
            machine_data["failed_attempts"] = 0
            if "remaining_attempts" in machine_data:
                machine_data.pop("remaining_attempts")
            if self.logger:
                self.logger.info(f"Successful login from {machine_info['hostname']} ({machine_info['ip_address']})")
        else:
            # Track failed attempts
            machine_data["failed_attempts"] += 1
            
            # Calculate remaining attempts based on previous lockouts
            max_attempts = max(1, self.max_login_attempts - machine_data.get("previous_lockouts", 0))
            remaining = max_attempts - machine_data["failed_attempts"]
            
            machine_data["remaining_attempts"] = remaining
            
            if self.logger:
                self.logger.warning(
                    f"Failed login attempt from {machine_info['hostname']} "
                    f"({machine_info['ip_address']}). "
                    f"Attempts remaining: {remaining}"
                )
            
            # If no remaining attempts, lock out the machine
            if remaining <= 0:
                lockout_time = datetime.now() + timedelta(seconds=self.lockout_duration)
                machine_data["lockout_until"] = lockout_time.strftime("%Y-%m-%d %H:%M:%S")
                if self.logger:
                    self.logger.warning(
                        f"Device locked out until {machine_data['lockout_until']} "
                        f"due to too many failed attempts"
                    )
        
        # Save updated data
        login_data[machine_id] = machine_data
        self._save_login_attempts(login_data)
        
        return machine_data
    
    def _load_login_attempts(self):
        """
        Load the login attempts data
        
        Returns:
            Dictionary with login attempt tracking data
        """
        try:
            with open(self.login_attempts_file, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError, KeyError):
            return {}
    
    def _save_login_attempts(self, data):
        """
        Save the login attempts data
        
        Args:
            data: Dictionary with login attempt tracking data
        """
        with open(self.login_attempts_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def start_session_checker(self):
        """Start a background thread to check for session timeout"""
        def check_session():
            while True:
                time.sleep(60)  # Check every minute
                if self.session_authenticated:
                    elapsed = time.time() - self.last_activity_time
                    if elapsed > self.session_timeout:
                        print("\n⚠️ Session timed out due to inactivity (30 minutes).")
                        print("Please authenticate again to continue.")
                        self.session_authenticated = False
        
        # Start the thread as daemon so it doesn't prevent program exit
        session_thread = threading.Thread(target=check_session, daemon=True)
        session_thread.start()
    
    def update_activity_time(self):
        """Update the last activity timestamp"""
        self.last_activity_time = time.time()
        
    def set_authenticated(self, username):
        """
        Set the session as authenticated
        
        Args:
            username: Authenticated username
        """
        self.session_authenticated = True
        self.username = username
        self.last_activity_time = time.time()
        
    def logout(self):
        """Log out the current session"""
        if self.logger and self.username:
            self.logger.info(f"User {self.username} logged out")
        self.session_authenticated = False
        self.username = None 