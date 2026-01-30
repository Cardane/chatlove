"""
Message models for Lovable Automation Service
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class MessageStatus(str, Enum):
    """Message processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class MessagePriority(str, Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ChatMessage(BaseModel):
    """Chat message from ChatLove to be processed by Lovable"""
    id: str = Field(..., description="Unique message identifier")
    user_id: str = Field(..., description="ChatLove user ID")
    project_id: str = Field(..., description="Lovable project ID")
    content: str = Field(..., description="Message content")
    
    # Context
    project_context: Dict[str, Any] = Field(default_factory=dict)
    files: Optional[List[Dict[str, Any]]] = None
    current_page: str = "index"
    view: str = "preview"
    
    # Processing
    status: MessageStatus = MessageStatus.PENDING
    priority: MessagePriority = MessagePriority.NORMAL
    retry_count: int = 0
    max_retries: int = 3
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Session assignment
    assigned_session_id: Optional[str] = None
    
    # Error tracking
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = Field(default_factory=dict)
    
    def mark_processing(self, session_id: str) -> None:
        """Mark message as being processed"""
        self.status = MessageStatus.PROCESSING
        self.assigned_session_id = session_id
        self.started_at = datetime.utcnow()
    
    def mark_completed(self) -> None:
        """Mark message as completed"""
        self.status = MessageStatus.COMPLETED
        self.completed_at = datetime.utcnow()
    
    def mark_failed(self, error: str, details: Dict[str, Any] = None) -> None:
        """Mark message as failed"""
        self.status = MessageStatus.FAILED
        self.error_message = error
        self.error_details = details or {}
        self.completed_at = datetime.utcnow()
    
    def mark_retrying(self) -> None:
        """Mark message for retry"""
        self.status = MessageStatus.RETRYING
        self.retry_count += 1
        self.assigned_session_id = None
    
    def can_retry(self) -> bool:
        """Check if message can be retried"""
        return self.retry_count < self.max_retries
    
    def processing_time(self) -> Optional[float]:
        """Get processing time in seconds"""
        if not self.started_at or not self.completed_at:
            return None
        
        return (self.completed_at - self.started_at).total_seconds()
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if message has expired (stuck in processing)"""
        if self.status != MessageStatus.PROCESSING or not self.started_at:
            return False
        
        elapsed = datetime.utcnow() - self.started_at
        return elapsed.total_seconds() > (timeout_minutes * 60)
    
    class Config:
        use_enum_values = True


class ChatResponse(BaseModel):
    """Response from Lovable for a chat message"""
    message_id: str = Field(..., description="Original message ID")
    success: bool = Field(..., description="Whether processing was successful")
    
    # Response data
    ai_message_id: Optional[str] = None
    response_content: Optional[str] = None
    code_changes: Optional[Dict[str, Any]] = None
    
    # Streaming data
    streaming_chunks: List[str] = Field(default_factory=list)
    is_streaming_complete: bool = False
    
    # Metadata
    processing_time: Optional[float] = None
    tokens_used: Optional[int] = None
    session_id: Optional[str] = None
    
    # Error information
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_streaming_chunk(self, chunk: str) -> None:
        """Add a streaming response chunk"""
        self.streaming_chunks.append(chunk)
    
    def mark_streaming_complete(self) -> None:
        """Mark streaming as complete"""
        self.is_streaming_complete = True
    
    def get_full_response(self) -> str:
        """Get full response by joining streaming chunks"""
        if self.response_content:
            return self.response_content
        
        return "".join(self.streaming_chunks)
    
    def mark_error(self, error_message: str, error_code: str = None) -> None:
        """Mark response as having an error"""
        self.success = False
        self.error_message = error_message
        self.error_code = error_code


class QueuedMessage(BaseModel):
    """Message in the processing queue"""
    message: ChatMessage
    queue_position: int = 0
    estimated_wait_time: Optional[int] = None  # seconds
    
    # Queue metadata
    queued_at: datetime = Field(default_factory=datetime.utcnow)
    priority_score: float = 0.0
    
    def calculate_priority_score(self) -> float:
        """Calculate priority score for queue ordering"""
        base_score = {
            MessagePriority.LOW: 1.0,
            MessagePriority.NORMAL: 2.0,
            MessagePriority.HIGH: 3.0,
            MessagePriority.URGENT: 4.0
        }.get(self.message.priority, 2.0)
        
        # Increase priority for retries
        retry_bonus = self.message.retry_count * 0.5
        
        # Decrease priority for age (older messages get lower priority)
        age_minutes = (datetime.utcnow() - self.message.created_at).total_seconds() / 60
        age_penalty = min(age_minutes * 0.01, 1.0)  # Max 1.0 penalty
        
        self.priority_score = base_score + retry_bonus - age_penalty
        return self.priority_score


class MessageBatch(BaseModel):
    """Batch of messages for bulk processing"""
    id: str = Field(..., description="Batch identifier")
    messages: List[ChatMessage] = Field(default_factory=list)
    
    # Batch settings
    max_size: int = 10
    timeout_seconds: int = 300  # 5 minutes
    
    # Status
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def add_message(self, message: ChatMessage) -> bool:
        """Add message to batch if there's space"""
        if len(self.messages) >= self.max_size:
            return False
        
        self.messages.append(message)
        return True
    
    def is_full(self) -> bool:
        """Check if batch is full"""
        return len(self.messages) >= self.max_size
    
    def is_ready(self) -> bool:
        """Check if batch is ready for processing"""
        if self.is_full():
            return True
        
        # Check timeout
        if self.messages:
            oldest_message = min(self.messages, key=lambda m: m.created_at)
            age = datetime.utcnow() - oldest_message.created_at
            return age.total_seconds() >= self.timeout_seconds
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batch statistics"""
        if not self.messages:
            return {"count": 0}
        
        statuses = {}
        for message in self.messages:
            status = message.status
            statuses[status] = statuses.get(status, 0) + 1
        
        return {
            "count": len(self.messages),
            "statuses": statuses,
            "oldest_message": min(self.messages, key=lambda m: m.created_at).created_at,
            "newest_message": max(self.messages, key=lambda m: m.created_at).created_at
        }
