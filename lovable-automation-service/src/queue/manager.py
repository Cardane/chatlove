"""
Queue Manager for Lovable Automation Service
"""

import asyncio
import uuid
from typing import Optional, List, Dict, Any, AsyncIterator
from datetime import datetime, timedelta
import redis.asyncio as redis
from collections import deque

from ..core.config import settings, get_redis_config
from ..core.exceptions import QueueError, QueueFullError, MessageProcessingError, RateLimitExceededError
from ..core.logging import LoggerMixin, log_queue_event
from ..models.message import ChatMessage, QueuedMessage, MessageStatus, MessagePriority, MessageBatch
from ..models.response import ChatLoveResponse


class LovableQueueManager(LoggerMixin):
    """
    Manages message queue with priority, rate limiting, and retry logic
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.local_queue: deque = deque()
        self.processing_messages: Dict[str, ChatMessage] = {}
        self.rate_limiter = RateLimiter(
            max_messages=settings.max_messages_per_minute,
            window_seconds=60
        )
        
        # Queue settings
        self.max_queue_size = 1000
        self.batch_size = 10
        self.processing_timeout = 300  # 5 minutes
        
        # Background tasks
        self._processor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start(self) -> None:
        """Start the queue manager"""
        if self._is_running:
            return
        
        self.logger.info("Starting Queue Manager")
        
        try:
            # Initialize Redis connection
            redis_config = get_redis_config()
            self.redis_client = redis.from_url(
                redis_config["url"],
                decode_responses=redis_config["decode_responses"]
            )
            
            # Test Redis connection
            await self.redis_client.ping()
            self.logger.info("Redis connection established")
            
        except Exception as e:
            self.logger.warning(f"Redis connection failed, using local queue: {str(e)}")
            self.redis_client = None
        
        self._is_running = True
        
        # Start background tasks
        self._processor_task = asyncio.create_task(self._process_queue_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.logger.info("Queue Manager started successfully")
    
    async def stop(self) -> None:
        """Stop the queue manager"""
        if not self._is_running:
            return
        
        self.logger.info("Stopping Queue Manager")
        self._is_running = False
        
        # Cancel background tasks
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        self.logger.info("Queue Manager stopped")
    
    async def enqueue_message(self, message: ChatMessage) -> str:
        """Add message to queue"""
        try:
            # Check rate limiting
            if not await self.rate_limiter.allow_request(message.user_id):
                raise RateLimitExceededError(f"Rate limit exceeded for user {message.user_id}")
            
            # Check queue size
            queue_size = await self.get_queue_size()
            if queue_size >= self.max_queue_size:
                raise QueueFullError("Message queue is full")
            
            # Create queued message
            queued_message = QueuedMessage(message=message)
            queued_message.calculate_priority_score()
            
            # Add to queue
            if self.redis_client:
                await self._enqueue_to_redis(queued_message)
            else:
                await self._enqueue_to_local(queued_message)
            
            log_queue_event(
                "message_enqueued",
                message.id,
                user_id=message.user_id,
                priority=message.priority,
                queue_size=queue_size + 1
            )
            
            return message.id
            
        except Exception as e:
            self.logger.error(f"Failed to enqueue message: {str(e)}")
            raise QueueError(f"Failed to enqueue message: {str(e)}")
    
    async def dequeue_message(self) -> Optional[ChatMessage]:
        """Get next message from queue"""
        try:
            if self.redis_client:
                return await self._dequeue_from_redis()
            else:
                return await self._dequeue_from_local()
        
        except Exception as e:
            self.logger.error(f"Failed to dequeue message: {str(e)}")
            return None
    
    async def mark_message_processing(self, message: ChatMessage, session_id: str) -> None:
        """Mark message as being processed"""
        message.mark_processing(session_id)
        self.processing_messages[message.id] = message
        
        log_queue_event(
            "message_processing",
            message.id,
            session_id=session_id,
            processing_count=len(self.processing_messages)
        )
    
    async def mark_message_completed(self, message: ChatMessage, response: ChatLoveResponse) -> None:
        """Mark message as completed"""
        message.mark_completed()
        
        # Remove from processing
        if message.id in self.processing_messages:
            del self.processing_messages[message.id]
        
        # Store result if using Redis
        if self.redis_client:
            await self._store_result(message.id, response)
        
        log_queue_event(
            "message_completed",
            message.id,
            processing_time=message.processing_time(),
            success=response.success
        )
    
    async def mark_message_failed(self, message: ChatMessage, error: str, retry: bool = True) -> None:
        """Mark message as failed"""
        message.mark_failed(error)
        
        # Remove from processing
        if message.id in self.processing_messages:
            del self.processing_messages[message.id]
        
        # Retry if allowed
        if retry and message.can_retry():
            message.mark_retrying()
            await self.enqueue_message(message)
            
            log_queue_event(
                "message_retry",
                message.id,
                retry_count=message.retry_count,
                error=error
            )
        else:
            log_queue_event(
                "message_failed",
                message.id,
                error=error,
                retry_count=message.retry_count
            )
    
    async def get_queue_size(self) -> int:
        """Get current queue size"""
        try:
            if self.redis_client:
                return await self.redis_client.llen("lovable_queue")
            else:
                return len(self.local_queue)
        except:
            return 0
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        queue_size = await self.get_queue_size()
        processing_count = len(self.processing_messages)
        
        # Calculate average wait time
        avg_wait_time = 0
        if queue_size > 0:
            avg_wait_time = (queue_size * 30)  # Estimate 30 seconds per message
        
        return {
            "queue_size": queue_size,
            "processing_count": processing_count,
            "max_queue_size": self.max_queue_size,
            "avg_wait_time_seconds": avg_wait_time,
            "rate_limit_remaining": await self.rate_limiter.get_remaining_quota(),
            "is_running": self._is_running
        }
    
    async def _enqueue_to_redis(self, queued_message: QueuedMessage) -> None:
        """Add message to Redis queue"""
        message_data = {
            "message": queued_message.message.dict(),
            "priority_score": queued_message.priority_score,
            "queued_at": queued_message.queued_at.isoformat()
        }
        
        # Use priority queue (sorted set)
        await self.redis_client.zadd(
            "lovable_priority_queue",
            {queued_message.message.id: queued_message.priority_score}
        )
        
        # Store message data
        await self.redis_client.hset(
            "lovable_messages",
            queued_message.message.id,
            queued_message.message.json()
        )
    
    async def _enqueue_to_local(self, queued_message: QueuedMessage) -> None:
        """Add message to local queue"""
        # Insert based on priority
        inserted = False
        for i, existing in enumerate(self.local_queue):
            if queued_message.priority_score > existing.priority_score:
                self.local_queue.insert(i, queued_message)
                inserted = True
                break
        
        if not inserted:
            self.local_queue.append(queued_message)
    
    async def _dequeue_from_redis(self) -> Optional[ChatMessage]:
        """Get next message from Redis queue"""
        try:
            # Get highest priority message
            result = await self.redis_client.zpopmax("lovable_priority_queue")
            
            if not result:
                return None
            
            message_id, priority_score = result[0]
            
            # Get message data
            message_data = await self.redis_client.hget("lovable_messages", message_id)
            
            if not message_data:
                return None
            
            # Parse message
            message = ChatMessage.parse_raw(message_data)
            
            # Remove from storage
            await self.redis_client.hdel("lovable_messages", message_id)
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error dequeuing from Redis: {str(e)}")
            return None
    
    async def _dequeue_from_local(self) -> Optional[ChatMessage]:
        """Get next message from local queue"""
        try:
            if not self.local_queue:
                return None
            
            queued_message = self.local_queue.popleft()
            return queued_message.message
            
        except Exception as e:
            self.logger.error(f"Error dequeuing from local queue: {str(e)}")
            return None
    
    async def _store_result(self, message_id: str, response: ChatLoveResponse) -> None:
        """Store processing result in Redis"""
        try:
            result_data = {
                "message_id": message_id,
                "response": response.dict(),
                "completed_at": datetime.utcnow().isoformat()
            }
            
            # Store with expiration (24 hours)
            await self.redis_client.setex(
                f"lovable_result:{message_id}",
                86400,  # 24 hours
                response.json()
            )
            
        except Exception as e:
            self.logger.error(f"Error storing result: {str(e)}")
    
    async def _process_queue_loop(self) -> None:
        """Background task to process queue"""
        while self._is_running:
            try:
                # Process messages in batches
                batch = await self._get_message_batch()
                
                if batch:
                    await self._process_message_batch(batch)
                else:
                    # No messages, wait a bit
                    await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in queue processing loop: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _cleanup_loop(self) -> None:
        """Background task to cleanup expired messages"""
        while self._is_running:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Cleanup expired processing messages
                expired_messages = []
                current_time = datetime.utcnow()
                
                for message_id, message in self.processing_messages.items():
                    if message.is_expired(timeout_minutes=self.processing_timeout // 60):
                        expired_messages.append(message_id)
                
                # Handle expired messages
                for message_id in expired_messages:
                    message = self.processing_messages[message_id]
                    await self.mark_message_failed(
                        message,
                        "Processing timeout",
                        retry=True
                    )
                
                if expired_messages:
                    self.logger.info(f"Cleaned up {len(expired_messages)} expired messages")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {str(e)}")
    
    async def _get_message_batch(self) -> List[ChatMessage]:
        """Get a batch of messages for processing"""
        batch = []
        
        for _ in range(self.batch_size):
            message = await self.dequeue_message()
            if message:
                batch.append(message)
            else:
                break
        
        return batch
    
    async def _process_message_batch(self, batch: List[ChatMessage]) -> None:
        """Process a batch of messages"""
        # This would be implemented to actually process messages
        # For now, just log that we received a batch
        self.logger.debug(f"Processing batch of {len(batch)} messages")
        
        # In real implementation, this would:
        # 1. Get available sessions
        # 2. Assign messages to sessions
        # 3. Process messages through browser automation
        # 4. Handle responses and errors


class RateLimiter:
    """Rate limiter for message processing"""
    
    def __init__(self, max_messages: int, window_seconds: int):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = {}
    
    async def allow_request(self, user_id: str) -> bool:
        """Check if request is allowed under rate limit"""
        now = datetime.utcnow()
        
        # Clean old requests
        if user_id in self.requests:
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if (now - req_time).total_seconds() < self.window_seconds
            ]
        else:
            self.requests[user_id] = []
        
        # Check if under limit
        if len(self.requests[user_id]) >= self.max_messages:
            return False
        
        # Add current request
        self.requests[user_id].append(now)
        return True
    
    async def get_remaining_quota(self, user_id: str = "global") -> int:
        """Get remaining quota for user"""
        if user_id not in self.requests:
            return self.max_messages
        
        now = datetime.utcnow()
        recent_requests = [
            req_time for req_time in self.requests[user_id]
            if (now - req_time).total_seconds() < self.window_seconds
        ]
        
        return max(0, self.max_messages - len(recent_requests))
