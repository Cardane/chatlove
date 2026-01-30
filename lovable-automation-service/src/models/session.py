"""
Session models for Lovable Automation Service
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class SessionStatus(str, Enum):
    """Session status enumeration"""
    INACTIVE = "inactive"
    AUTHENTICATING = "authenticating"
    ACTIVE = "active"
    EXPIRED = "expired"
    ERROR = "error"


class Account(BaseModel):
    """Lovable account credentials"""
    email: str
    password: str
    display_name: Optional[str] = None
    
    class Config:
        # Don't include password in string representation
        fields = {"password": {"write_only": True}}


class Session(BaseModel):
    """Lovable session model"""
    id: str = Field(..., description="Unique session identifier")
    account: Account
    status: SessionStatus = SessionStatus.INACTIVE
    
    # Authentication data
    firebase_token: Optional[str] = None
    session_cookies: Dict[str, Any] = Field(default_factory=dict)
    user_agent: Optional[str] = None
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    authenticated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    
    # Usage tracking
    message_count: int = 0
    error_count: int = 0
    
    # Browser context
    browser_context_id: Optional[str] = None
    page_url: Optional[str] = None
    
    def is_active(self) -> bool:
        """Check if session is active and not expired"""
        if self.status != SessionStatus.ACTIVE:
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        return True
    
    def is_expired(self) -> bool:
        """Check if session has expired"""
        if not self.expires_at:
            return False
        
        return datetime.utcnow() > self.expires_at
    
    def time_until_expiry(self) -> Optional[timedelta]:
        """Get time until session expires"""
        if not self.expires_at:
            return None
        
        return self.expires_at - datetime.utcnow()
    
    def update_last_used(self) -> None:
        """Update last used timestamp"""
        self.last_used_at = datetime.utcnow()
    
    def increment_message_count(self) -> None:
        """Increment message count and update last used"""
        self.message_count += 1
        self.update_last_used()
    
    def increment_error_count(self) -> None:
        """Increment error count"""
        self.error_count += 1
    
    def mark_authenticated(self, firebase_token: str, cookies: Dict[str, Any]) -> None:
        """Mark session as authenticated"""
        self.status = SessionStatus.ACTIVE
        self.firebase_token = firebase_token
        self.session_cookies = cookies
        self.authenticated_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=24)  # Default 24h expiry
    
    def mark_expired(self) -> None:
        """Mark session as expired"""
        self.status = SessionStatus.EXPIRED
    
    def mark_error(self) -> None:
        """Mark session as having an error"""
        self.status = SessionStatus.ERROR
        self.increment_error_count()
    
    class Config:
        use_enum_values = True


class SessionPool(BaseModel):
    """Pool of Lovable sessions"""
    sessions: List[Session] = Field(default_factory=list)
    max_sessions: int = 5
    current_index: int = 0
    
    def add_session(self, session: Session) -> None:
        """Add session to pool"""
        if len(self.sessions) >= self.max_sessions:
            # Remove oldest inactive session
            inactive_sessions = [s for s in self.sessions if not s.is_active()]
            if inactive_sessions:
                oldest = min(inactive_sessions, key=lambda s: s.created_at)
                self.sessions.remove(oldest)
            else:
                raise ValueError("Session pool is full and all sessions are active")
        
        self.sessions.append(session)
    
    def get_active_session(self) -> Optional[Session]:
        """Get next available active session using round-robin"""
        active_sessions = [s for s in self.sessions if s.is_active()]
        
        if not active_sessions:
            return None
        
        # Round-robin selection
        session = active_sessions[self.current_index % len(active_sessions)]
        self.current_index = (self.current_index + 1) % len(active_sessions)
        
        return session
    
    def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        for session in self.sessions:
            if session.id == session_id:
                return session
        return None
    
    def remove_session(self, session_id: str) -> bool:
        """Remove session from pool"""
        for i, session in enumerate(self.sessions):
            if session.id == session_id:
                del self.sessions[i]
                return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions and return count removed"""
        initial_count = len(self.sessions)
        self.sessions = [s for s in self.sessions if not s.is_expired()]
        return initial_count - len(self.sessions)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        total = len(self.sessions)
        active = len([s for s in self.sessions if s.is_active()])
        expired = len([s for s in self.sessions if s.is_expired()])
        error = len([s for s in self.sessions if s.status == SessionStatus.ERROR])
        
        return {
            "total_sessions": total,
            "active_sessions": active,
            "expired_sessions": expired,
            "error_sessions": error,
            "utilization": active / self.max_sessions if self.max_sessions > 0 else 0
        }
    
    def get_least_used_session(self) -> Optional[Session]:
        """Get the active session with lowest message count"""
        active_sessions = [s for s in self.sessions if s.is_active()]
        
        if not active_sessions:
            return None
        
        return min(active_sessions, key=lambda s: s.message_count)
    
    def get_session_by_account(self, email: str) -> Optional[Session]:
        """Get session by account email"""
        for session in self.sessions:
            if session.account.email == email:
                return session
        return None
