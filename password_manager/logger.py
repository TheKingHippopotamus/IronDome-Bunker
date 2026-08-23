#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Logging module for IronDome"""

import logging

from password_manager.secure_io import ensure_secure_file

def setup_logger(log_file):
    """
    Set up the logging system
    
    Args:
        log_file: Path to the log file
        
    Returns:
        Logger instance
    """
    # Create logger
    logger = logging.getLogger("SecurePasswordManager")
    logger.setLevel(logging.INFO)
    
    # The log records vault activity -- entry names, timestamps, failures --
    # so it is created 0600 before logging opens it for append.
    ensure_secure_file(log_file)

    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    return logger 