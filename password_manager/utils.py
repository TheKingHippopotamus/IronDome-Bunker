#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Utility functions for the Secure Password Manager"""

import getpass
import re
import socket
import platform
import uuid
import os
from datetime import datetime

def get_validated_input(prompt, valid_options=None, valid_pattern=None, default=None, allow_back=True, logger=None):
    """
    Get user input with validation
    
    Args:
        prompt: Text to display to the user
        valid_options: List of valid input options (case insensitive)
        valid_pattern: Regex pattern that input must match
        default: Default value if user enters nothing
        allow_back: Whether to allow 'b' or 'back' as input to go back
        logger: Optional logger instance to log input
        
    Returns:
        User input string or '_BACK_' for back command
    """
    # Add back option notice if allowed
    if allow_back:
        if prompt.strip().endswith(':'):
            prompt = prompt.strip() + " (or 'b' to go back): "
        else:
            prompt = prompt.strip() + " (or enter 'b' to go back): "
            
    while True:
        user_input = input(prompt)
        
        # Check for back command
        if allow_back and user_input.lower() in ['b', 'back']:
            return '_BACK_'
            
        # Use default if input is empty and default is provided
        if not user_input and default is not None:
            return default
            
        # Validate against valid options
        if valid_options and user_input.lower() not in valid_options:
            print(f"⚠️ Invalid input. Valid options are: {', '.join(valid_options)}")
            continue
            
        # Validate against pattern
        if valid_pattern and not re.match(valid_pattern, user_input):
            print(f"⚠️ Invalid input. Must match pattern: {valid_pattern}")
            continue
        
        # Log input (but not passwords or sensitive data)
        if logger and not any(s in prompt.lower() for s in ["password", "secret", "master"]):
            logger.debug(f"User input: {prompt.split(':')[0]} = {user_input}")
            
        return user_input.lower() if valid_options else user_input

def get_validated_int(prompt, min_value=None, max_value=None, default=None, allow_back=True, logger=None):
    """
    Get integer input with validation
    
    Args:
        prompt: Text to display to the user
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        default: Default value if user enters nothing
        allow_back: Whether to allow 'b' or 'back' as input to go back
        logger: Optional logger instance to log input
        
    Returns:
        Integer value or '_BACK_' for back command
    """
    # Add back option notice
    if allow_back:
        if prompt.strip().endswith(':'):
            prompt = prompt.strip() + " (or 'b' to go back): "
        else:
            prompt = prompt.strip() + " (or enter 'b' to go back): "
            
    while True:
        user_input = input(prompt)
        
        # Check for back command
        if allow_back and user_input.lower() in ['b', 'back']:
            return '_BACK_'
            
        # Use default if input is empty and default is provided
        if not user_input and default is not None:
            return default
            
        # Validate that input is an integer
        try:
            value = int(user_input)
        except ValueError:
            print("⚠️ Please enter a valid number.")
            continue
            
        # Validate minimum value
        if min_value is not None and value < min_value:
            print(f"⚠️ Value must be at least {min_value}.")
            continue
            
        # Validate maximum value
        if max_value is not None and value > max_value:
            print(f"⚠️ Value must be no more than {max_value}.")
            continue
            
        return value

def extract_domain_name(url):
    """
    Extract the domain name from a URL, removing protocol and common TLDs
    
    Args:
        url: The URL string to process
        
    Returns:
        The extracted domain name
    """
    # Remove protocol (http://, https://)
    if '://' in url:
        url = url.split('://', 1)[1]
    
    # Remove "www." if present
    if url.startswith('www.'):
        url = url[4:]
    
    # Remove path after domain (everything after first /)
    if '/' in url:
        url = url.split('/', 1)[0]
    
    # Remove port if present (everything after :)
    if ':' in url:
        url = url.split(':', 1)[0]
    
    # Remove common TLDs
    common_tlds = ['.com', '.org', '.net', '.edu', '.gov', '.co', '.io']
    for tld in common_tlds:
        if url.endswith(tld):
            url = url[:-len(tld)]
            break
        
    return url

def get_machine_info():
    """
    Get detailed information about the current machine
    
    Returns:
        Dictionary with machine information
    """
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        os_info = f"{platform.system()} {platform.release()}"
        mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                               for elements in range(0, 8*6, 8)][::-1])
        
        return {
            "hostname": hostname,
            "ip_address": ip_address,
            "os_info": os_info,
            "mac_address": mac_address,
            "username": getpass.getuser(),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        # Provide fallback values so callers don't crash on missing keys
        mac_fallback = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                                 for elements in range(0, 8*6, 8)][::-1])
        return {
            "hostname": "unknown",
            "ip_address": "unknown",
            "os_info": f"{platform.system()} {platform.release()}",
            "mac_address": mac_fallback,
            "username": getpass.getuser(),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        } 