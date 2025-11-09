"""
Colored logger configuration for the Bollette Agent.
Provides different colors for different log levels for better readability.
"""

import logging
import sys
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""
    
    # Define colors for each log level
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }
    
    def format(self, record):
        # Save the original format
        log_color = self.COLORS.get(record.levelname, Fore.WHITE)
        
        # Format the level name with color
        levelname = f"{log_color}{record.levelname:8}{Style.RESET_ALL}"
        
        # Format the message with a subtle color
        message = f"{log_color}{record.getMessage()}{Style.RESET_ALL}"
        
        # Format the logger name in a different color
        name = f"{Fore.MAGENTA}{record.name}{Style.RESET_ALL}"
        
        # Create the formatted message
        formatted = f"{levelname} | {name} | {message}"
        
        return formatted


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with colored output.
    
    Args:
        name: Name of the logger (usually __name__)
        level: Logging level (default: logging.INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create and set formatter
    formatter = ColoredFormatter()
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger
