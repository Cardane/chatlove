"""
Response models for Lovable Automation Service
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from enum import Enum


class ResponseType(str, Enum):
    """Type of response from Lovable"""
    CHAT = "chat"
    CODE_GENERATION = "code_generation"
    FILE_UPDATE = "file_update"
    ERROR = "error"
    STREAMING = "streaming"


class StreamingChunkType(str, Enum):
    """Type of streaming chunk"""
    TEXT = "text"
    CODE = "code"
    FILE_CHANGE = "file_change"
    METADATA = "metadata"
    ERROR = "error"
    COMPLETE = "complete"


class StreamingChunk(BaseModel):
    """Individual chunk from streaming response"""
    id: str = Field(..., description="Chunk identifier")
    type: StreamingChunkType
    content: str = Field(..., description="Chunk content")
    
    # Metadata
    sequence: int = Field(..., description="Sequence number in stream")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Optional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def is_complete(self) -> bool:
        """Check if this is a completion chunk"""
        return self.type == StreamingChunkType.COMPLETE


class FileChange(BaseModel):
    """Represents a file change from Lovable"""
    file_path: str = Field(..., description="Path to the file")
    action: str = Field(..., description="Action: create, update, delete")
    content: Optional[str] = None
    diff: Optional[str] = None
    
    # Metadata
    line_count: Optional[int] = None
    size_bytes: Optional[int] = None
    encoding: str = "utf-8"
    
    def is_creation(self) -> bool:
        """Check if this is a file creation"""
        return self.action.lower() == "create"
    
    def is_update(self) -> bool:
        """Check if this is a file update"""
        return self.action.lower() == "update"
    
    def is_deletion(self) -> bool:
        """Check if this is a file deletion"""
        return self.action.lower() == "delete"


class CodeChanges(BaseModel):
    """Collection of code changes from Lovable"""
    files: List[FileChange] = Field(default_factory=list)
    summary: Optional[str] = None
    
    # Statistics
    files_created: int = 0
    files_updated: int = 0
    files_deleted: int = 0
    total_lines_added: int = 0
    total_lines_removed: int = 0
    
    def add_file_change(self, file_change: FileChange) -> None:
        """Add a file change and update statistics"""
        self.files.append(file_change)
        
        if file_change.is_creation():
            self.files_created += 1
        elif file_change.is_update():
            self.files_updated += 1
        elif file_change.is_deletion():
            self.files_deleted += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get change statistics"""
        return {
            "total_files": len(self.files),
            "files_created": self.files_created,
            "files_updated": self.files_updated,
            "files_deleted": self.files_deleted,
            "total_lines_added": self.total_lines_added,
            "total_lines_removed": self.total_lines_removed
        }
    
    def get_file_paths(self) -> List[str]:
        """Get list of all affected file paths"""
        return [f.file_path for f in self.files]


class LovableResponse(BaseModel):
    """Complete response from Lovable API"""
    message_id: str = Field(..., description="Original message ID")
    ai_message_id: Optional[str] = None
    type: ResponseType = ResponseType.CHAT
    
    # Response content
    content: Optional[str] = None
    code_changes: Optional[CodeChanges] = None
    
    # Streaming data
    streaming_chunks: List[StreamingChunk] = Field(default_factory=list)
    is_streaming: bool = False
    is_streaming_complete: bool = False
    
    # Metadata
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    processing_time: Optional[float] = None
    
    # Status
    success: bool = True
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def add_streaming_chunk(self, chunk: StreamingChunk) -> None:
        """Add a streaming chunk"""
        self.streaming_chunks.append(chunk)
        self.is_streaming = True
        
        if chunk.is_complete():
            self.is_streaming_complete = True
            self.completed_at = datetime.utcnow()
    
    def get_full_content(self) -> str:
        """Get full content from streaming chunks or direct content"""
        if self.content:
            return self.content
        
        # Combine text chunks
        text_chunks = [
            chunk.content for chunk in self.streaming_chunks
            if chunk.type == StreamingChunkType.TEXT
        ]
        
        return "".join(text_chunks)
    
    def get_code_chunks(self) -> List[StreamingChunk]:
        """Get all code-related chunks"""
        return [
            chunk for chunk in self.streaming_chunks
            if chunk.type in [StreamingChunkType.CODE, StreamingChunkType.FILE_CHANGE]
        ]
    
    def mark_error(self, error_message: str, error_code: str = None) -> None:
        """Mark response as having an error"""
        self.success = False
        self.error_message = error_message
        self.error_code = error_code
        self.type = ResponseType.ERROR
        self.completed_at = datetime.utcnow()
    
    def mark_complete(self) -> None:
        """Mark response as complete"""
        self.is_streaming_complete = True
        self.completed_at = datetime.utcnow()
    
    def get_processing_duration(self) -> Optional[float]:
        """Get total processing duration in seconds"""
        if not self.completed_at:
            return None
        
        return (self.completed_at - self.created_at).total_seconds()


class ChatLoveResponse(BaseModel):
    """Response formatted for ChatLove frontend"""
    success: bool = True
    message: str = ""
    
    # Data
    response_content: Optional[str] = None
    code_changes: Optional[Dict[str, Any]] = None
    
    # Metadata
    tokens_saved: Optional[float] = None
    processing_time: Optional[float] = None
    session_id: Optional[str] = None
    
    # Streaming support
    streaming_url: Optional[str] = None
    is_streaming: bool = False
    
    # Error information
    error_code: Optional[str] = None
    error_details: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def from_lovable_response(cls, lovable_response: LovableResponse, tokens_saved: float = None) -> "ChatLoveResponse":
        """Create ChatLove response from Lovable response"""
        if not lovable_response.success:
            return cls(
                success=False,
                message=lovable_response.error_message or "Erro ao processar mensagem",
                error_code=lovable_response.error_code,
                error_details={"lovable_error": True}
            )
        
        # Convert code changes to dict
        code_changes_dict = None
        if lovable_response.code_changes:
            code_changes_dict = {
                "files": [
                    {
                        "path": fc.file_path,
                        "action": fc.action,
                        "content": fc.content,
                        "diff": fc.diff
                    }
                    for fc in lovable_response.code_changes.files
                ],
                "stats": lovable_response.code_changes.get_stats()
            }
        
        return cls(
            success=True,
            message="Mensagem processada com sucesso",
            response_content=lovable_response.get_full_content(),
            code_changes=code_changes_dict,
            tokens_saved=tokens_saved,
            processing_time=lovable_response.get_processing_duration(),
            is_streaming=lovable_response.is_streaming
        )
    
    @classmethod
    def error(cls, message: str, error_code: str = None, details: Dict[str, Any] = None) -> "ChatLoveResponse":
        """Create error response"""
        return cls(
            success=False,
            message=message,
            error_code=error_code,
            error_details=details or {}
        )


class ResponseMetrics(BaseModel):
    """Metrics for response analysis"""
    response_id: str
    
    # Timing metrics
    queue_time: Optional[float] = None  # Time in queue
    processing_time: Optional[float] = None  # Time to process
    total_time: Optional[float] = None  # Total time
    
    # Content metrics
    input_length: int = 0
    output_length: int = 0
    tokens_estimated: Optional[int] = None
    
    # Quality metrics
    success_rate: float = 1.0
    retry_count: int = 0
    error_count: int = 0
    
    # Session metrics
    session_id: Optional[str] = None
    session_message_count: Optional[int] = None
    
    def calculate_efficiency_score(self) -> float:
        """Calculate efficiency score (0-1)"""
        if not self.total_time or self.total_time <= 0:
            return 0.0
        
        # Base score from success rate
        base_score = self.success_rate
        
        # Penalty for retries
        retry_penalty = min(self.retry_count * 0.1, 0.5)
        
        # Bonus for fast processing (under 10 seconds)
        speed_bonus = 0.0
        if self.total_time < 10:
            speed_bonus = (10 - self.total_time) / 10 * 0.2
        
        return max(0.0, min(1.0, base_score - retry_penalty + speed_bonus))
