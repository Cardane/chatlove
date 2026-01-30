"""
Session management module for Lovable Automation Service
"""

from .manager import LovableSessionManager
from .auth import FirebaseAuthenticator
from .pool import SessionPoolManager

__all__ = [
    "LovableSessionManager",
    "FirebaseAuthenticator", 
    "SessionPoolManager"
]
