"""
Core module for Lovable Automation Service
"""

from .config import settings
from .exceptions import LovableAutomationError, SessionError, BrowserError, QueueError
from .logging import setup_logging

__all__ = [
    "settings",
    "LovableAutomationError",
    "SessionError", 
    "BrowserError",
    "QueueError",
    "setup_logging"
]
