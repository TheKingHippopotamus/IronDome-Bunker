#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Logging module for IronDome"""

import logging
import os

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
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    return logger 