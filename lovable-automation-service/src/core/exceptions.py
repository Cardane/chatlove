"""
Custom exceptions for Lovable Automation Service
"""


class LovableAutomationError(Exception):
    """Base exception for Lovable Automation Service"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class SessionError(LovableAutomationError):
    """Session management related errors"""
    pass


class AuthenticationError(SessionError):
    """Authentication failed"""
    pass


class SessionExpiredError(SessionError):
    """Session has expired"""
    pass


class SessionPoolExhaustedError(SessionError):
    """No available sessions in pool"""
    pass


class BrowserError(LovableAutomationError):
    """Browser automation related errors"""
    pass


class BrowserLaunchError(BrowserError):
    """Failed to launch browser"""
    pass


class NavigationError(BrowserError):
    """Failed to navigate to page"""
    pass


class ElementNotFoundError(BrowserError):
    """Required element not found on page"""
    pass


class InterceptionError(BrowserError):
    """Failed to intercept network traffic"""
    pass


class QueueError(LovableAutomationError):
    """Queue management related errors"""
    pass


class QueueFullError(QueueError):
    """Queue is full"""
    pass


class MessageProcessingError(QueueError):
    """Failed to process message"""
    pass


class RateLimitExceededError(QueueError):
    """Rate limit exceeded"""
    pass


class APIError(LovableAutomationError):
    """API related errors"""
    pass


class LovableAPIError(APIError):
    """Lovable API returned an error"""
    pass


class ResponseParsingError(APIError):
    """Failed to parse API response"""
    pass


class DatabaseError(LovableAutomationError):
    """Database related errors"""
    pass


class ConfigurationError(LovableAutomationError):
    """Configuration related errors"""
    pass


class ValidationError(LovableAutomationError):
    """Data validation errors"""
    pass
