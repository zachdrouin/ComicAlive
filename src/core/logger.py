"""
Logger module for the Motion Comic Generator application
"""
import logging
import os
from datetime import datetime

def setup_logging(log_level=logging.INFO):
    """
    Set up logging for the application
    
    Args:
        log_level: The logging level to use
    """
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Set up logging configuration
    log_filename = f"logs/motion_comic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Configure logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    
    # Create logger
    logger = logging.getLogger('motion_comic')
    logger.info("Logging initialized")
    
    return logger
