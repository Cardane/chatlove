"""
Logging configuration for Lovable Automation Service
"""

import logging
import structlog
from typing import Any, Dict
from .config import settings


def setup_logging() -> None:
    """Setup structured logging with structlog"""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=None,
        level=getattr(logging, settings.log_level.upper())
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin to add logging capabilities to classes"""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger for this class"""
        return get_logger(self.__class__.__name__)


def log_session_event(event: str, session_id: str, **kwargs) -> None:
    """Log session-related events"""
    logger = get_logger("session")
    logger.info(
        "session_event",
        event=event,
        session_id=session_id,
        **kwargs
    )


def log_browser_event(event: str, browser_id: str, **kwargs) -> None:
    """Log browser-related events"""
    logger = get_logger("browser")
    logger.info(
        "browser_event",
        event=event,
        browser_id=browser_id,
        **kwargs
    )


def log_queue_event(event: str, message_id: str, **kwargs) -> None:
    """Log queue-related events"""
    logger = get_logger("queue")
    logger.info(
        "queue_event",
        event=event,
        message_id=message_id,
        **kwargs
    )


def log_api_event(event: str, endpoint: str, **kwargs) -> None:
    """Log API-related events"""
    logger = get_logger("api")
    logger.info(
        "api_event",
        event=event,
        endpoint=endpoint,
        **kwargs
    )


def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """Log errors with context"""
    logger = get_logger("error")
    logger.error(
        "error_occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {},
        exc_info=True
    )
