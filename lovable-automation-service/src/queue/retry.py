"""
Retry Manager for Lovable Automation Service
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from enum import Enum

from ..core.logging import LoggerMixin, log_queue_event
from ..models.message import ChatMessage, MessageStatus


class RetryStrategy(str, Enum):
    """Retry strategy types"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"


class RetryManager(LoggerMixin):
    """
    Manages retry logic for failed messages
    """
    
    def __init__(self):
        self.retry_queue: Dict[str, RetryItem] = {}
        self.retry_strategies: Dict[RetryStrategy, Callable] = {
            RetryStrategy.EXPONENTIAL_BACKOFF: self._exponential_backoff,
            RetryStrategy.LINEAR_BACKOFF: self._linear_backoff,
            RetryStrategy.FIXED_DELAY: self._fixed_delay,
            RetryStrategy.IMMEDIATE: self._immediate
        }
        
        # Default retry configuration
        self.default_config = RetryConfig(
            max_retries=3,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=5,  # seconds
            max_delay=300,  # 5 minutes
            backoff_multiplier=2.0
        )
        
        # Background task
        self._retry_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start(self) -> None:
        """Start the retry manager"""
        if self._is_running:
            return
        
        self.logger.info("Starting Retry Manager")
        self._is_running = True
        
        # Start background retry task
        self._retry_task = asyncio.create_task(self._retry_loop())
        
        self.logger.info("Retry Manager started successfully")
    
    async def stop(self) -> None:
        """Stop the retry manager"""
        if not self._is_running:
            return
        
        self.logger.info("Stopping Retry Manager")
        self._is_running = False
        
        # Cancel retry task
        if self._retry_task:
            self._retry_task.cancel()
            try:
                await self._retry_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Retry Manager stopped")
    
    async def schedule_retry(
        self, 
        message: ChatMessage, 
        error: str, 
        config: Optional['RetryConfig'] = None
    ) -> bool:
        """Schedule a message for retry"""
        try:
            # Use default config if none provided
            if not config:
                config = self.default_config
            
            # Check if message can be retried
            if not message.can_retry():
                self.logger.warning(f"Message {message.id} has exceeded max retries")
                return False
            
            # Calculate next retry time
            retry_delay = self._calculate_retry_delay(message, config)
            next_retry = datetime.utcnow() + timedelta(seconds=retry_delay)
            
            # Create retry item
            retry_item = RetryItem(
                message=message,
                error=error,
                config=config,
                next_retry=next_retry,
                retry_delay=retry_delay
            )
            
            # Add to retry queue
            self.retry_queue[message.id] = retry_item
            
            log_queue_event(
                "retry_scheduled",
                message.id,
                retry_count=message.retry_count,
                retry_delay=retry_delay,
                next_retry=next_retry.isoformat(),
                error=error
            )
            
            self.logger.info(
                f"Scheduled retry for message {message.id} in {retry_delay} seconds "
                f"(attempt {message.retry_count + 1}/{config.max_retries})"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to schedule retry for message {message.id}: {str(e)}")
            return False
    
    async def cancel_retry(self, message_id: str) -> bool:
        """Cancel a scheduled retry"""
        if message_id in self.retry_queue:
            retry_item = self.retry_queue[message_id]
            del self.retry_queue[message_id]
            
            log_queue_event("retry_cancelled", message_id)
            
            self.logger.info(f"Cancelled retry for message {message_id}")
            return True
        
        return False
    
    async def get_retry_stats(self) -> Dict[str, Any]:
        """Get retry statistics"""
        total_retries = len(self.retry_queue)
        
        # Count by retry attempt
        retry_counts = {}
        overdue_retries = 0
        now = datetime.utcnow()
        
        for retry_item in self.retry_queue.values():
            retry_count = retry_item.message.retry_count
            retry_counts[retry_count] = retry_counts.get(retry_count, 0) + 1
            
            if retry_item.next_retry <= now:
                overdue_retries += 1
        
        return {
            "total_retries": total_retries,
            "overdue_retries": overdue_retries,
            "retry_counts": retry_counts,
            "is_running": self._is_running
        }
    
    def _calculate_retry_delay(self, message: ChatMessage, config: 'RetryConfig') -> float:
        """Calculate delay for next retry"""
        strategy_func = self.retry_strategies.get(config.strategy, self._exponential_backoff)
        delay = strategy_func(message.retry_count, config)
        
        # Ensure delay is within bounds
        return min(max(delay, 1), config.max_delay)
    
    def _exponential_backoff(self, retry_count: int, config: 'RetryConfig') -> float:
        """Calculate exponential backoff delay"""
        return config.base_delay * (config.backoff_multiplier ** retry_count)
    
    def _linear_backoff(self, retry_count: int, config: 'RetryConfig') -> float:
        """Calculate linear backoff delay"""
        return config.base_delay * (retry_count + 1)
    
    def _fixed_delay(self, retry_count: int, config: 'RetryConfig') -> float:
        """Calculate fixed delay"""
        return config.base_delay
    
    def _immediate(self, retry_count: int, config: 'RetryConfig') -> float:
        """No delay (immediate retry)"""
        return 0
    
    async def _retry_loop(self) -> None:
        """Background task to process retry queue"""
        while self._is_running:
            try:
                await asyncio.sleep(1)  # Check every second
                
                # Get messages ready for retry
                ready_messages = await self._get_ready_retries()
                
                for retry_item in ready_messages:
                    await self._process_retry(retry_item)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in retry loop: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _get_ready_retries(self) -> List['RetryItem']:
        """Get messages that are ready for retry"""
        ready_messages = []
        now = datetime.utcnow()
        
        for message_id, retry_item in list(self.retry_queue.items()):
            if retry_item.next_retry <= now:
                ready_messages.append(retry_item)
                # Remove from queue
                del self.retry_queue[message_id]
        
        return ready_messages
    
    async def _process_retry(self, retry_item: 'RetryItem') -> None:
        """Process a retry item"""
        try:
            message = retry_item.message
            
            # Increment retry count
            message.retry_count += 1
            
            # Mark as retrying
            message.mark_retrying()
            
            log_queue_event(
                "retry_processing",
                message.id,
                retry_count=message.retry_count,
                original_error=retry_item.error
            )
            
            self.logger.info(f"Processing retry for message {message.id} (attempt {message.retry_count})")
            
            # Here you would re-enqueue the message for processing
            # This would typically involve calling the queue manager
            # For now, we'll just log that the retry is being processed
            
        except Exception as e:
            self.logger.error(f"Error processing retry for message {retry_item.message.id}: {str(e)}")


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_retries: int = 3,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay: float = 5.0,
        max_delay: float = 300.0,
        backoff_multiplier: float = 2.0
    ):
        self.max_retries = max_retries
        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier


class RetryItem:
    """Item in the retry queue"""
    
    def __init__(
        self,
        message: ChatMessage,
        error: str,
        config: RetryConfig,
        next_retry: datetime,
        retry_delay: float
    ):
        self.message = message
        self.error = error
        self.config = config
        self.next_retry = next_retry
        self.retry_delay = retry_delay
        self.created_at = datetime.utcnow()
    
    def is_ready(self) -> bool:
        """Check if retry is ready to be processed"""
        return datetime.utcnow() >= self.next_retry
    
    def time_until_retry(self) -> float:
        """Get seconds until retry is ready"""
        delta = self.next_retry - datetime.utcnow()
        return max(0, delta.total_seconds())


# Predefined retry configurations
class RetryConfigs:
    """Predefined retry configurations for different scenarios"""
    
    # Quick retry for temporary failures
    QUICK_RETRY = RetryConfig(
        max_retries=2,
        strategy=RetryStrategy.FIXED_DELAY,
        base_delay=5,
        max_delay=30
    )
    
    # Standard retry for most failures
    STANDARD_RETRY = RetryConfig(
        max_retries=3,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=10,
        max_delay=300,
        backoff_multiplier=2.0
    )
    
    # Aggressive retry for critical messages
    AGGRESSIVE_RETRY = RetryConfig(
        max_retries=5,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=5,
        max_delay=600,
        backoff_multiplier=1.5
    )
    
    # Conservative retry for rate-limited scenarios
    CONSERVATIVE_RETRY = RetryConfig(
        max_retries=3,
        strategy=RetryStrategy.LINEAR_BACKOFF,
        base_delay=60,
        max_delay=1800,  # 30 minutes
        backoff_multiplier=1.0
    )
