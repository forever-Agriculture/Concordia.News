"""
Logging utilities for the Concordia news sentiment analysis platform.

This module provides standardized logging configuration for different components
of the application, ensuring consistent log formatting and separation of concerns.
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logger(name, log_file, level=logging.INFO):
    """
    Set up a logger with a specific name and file.
    
    Args:
        name (str): Name of the logger
        log_file (str): Path to the log file
        level (int): Logging level (default: INFO)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create handler with rotation (10 MB max size, keep 5 backup files)
    handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    handler.setFormatter(formatter)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    logger.addHandler(handler)
    return logger


# Create loggers for different components
collector_logger = setup_logger('collector', 'logs/collector.log')
analyzer_logger = setup_logger('analyzer', 'logs/analyzer.log')
api_logger = setup_logger('api', 'logs/api.log')
media_logger = setup_logger('media', 'logs/media.log')
maintenance_logger = setup_logger('maintenance', 'logs/maintenance.log')
health_logger = setup_logger('health', 'logs/health.log') 