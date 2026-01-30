"""
Session Manager for Lovable Automation Service
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from ..core.config import settings, get_lovable_accounts
from ..core.exceptions import (
    SessionError, AuthenticationError, SessionExpiredError, 
    SessionPoolExhaustedError
)
from ..core.logging import LoggerMixin, log_session_event
from ..models.session import Session, SessionPool, Account, SessionStatus
from .auth import FirebaseAuthenticator
from .pool import SessionPoolManager


class LovableSessionManager(LoggerMixin):
    """
    Manages Lovable sessions with automatic authentication,
    refresh, and pool management
    """
    
    def __init__(self):
        self.authenticator = FirebaseAuthenticator()
        self.pool_manager = SessionPoolManager(max_sessions=settings.max_concurrent_sessions)
        self.accounts = [Account(**acc) for acc in get_lovable_accounts()]
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start(self) -> None:
        """Start the session manager"""
        if self._is_running:
            return
        
        self.logger.info("Starting Lovable Session Manager")
        self._is_running = True
        
        # Initialize sessions for all accounts
        await self._initialize_sessions()
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.logger.info(
            "Session manager started",
            accounts_count=len(self.accounts),
            max_sessions=settings.max_concurrent_sessions
        )
    
    async def stop(self) -> None:
        """Stop the session manager"""
        if not self._is_running:
            return
        
        self.logger.info("Stopping Lovable Session Manager")
        self._is_running = False
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close all sessions
        await self.pool_manager.close_all_sessions()
        
        self.logger.info("Session manager stopped")
    
    async def _initialize_sessions(self) -> None:
        """Initialize sessions for all configured accounts"""
        if not self.accounts:
            self.logger.warning("No Lovable accounts configured")
            return
        
        tasks = []
        for account in self.accounts:
            task = asyncio.create_task(self._create_session_for_account(account))
            tasks.append(task)
        
        # Wait for all sessions to be created (with timeout)
        try:
            await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=60.0)
        except asyncio.TimeoutError:
            self.logger.error("Timeout initializing sessions")
    
    async def _create_session_for_account(self, account: Account) -> Optional[Session]:
        """Create and authenticate a session for an account"""
        try:
            session_id = str(uuid.uuid4())
            session = Session(id=session_id, account=account)
            
            log_session_event("creating", session_id, email=account.email)
            
            # Authenticate the session
            await self.authenticate_session(session)
            
            # Add to pool
            self.pool_manager.add_session(session)
            
            log_session_event("created", session_id, status=session.status)
            return session
            
        except Exception as e:
            self.logger.error(
                "Failed to create session for account",
                email=account.email,
                error=str(e)
            )
            return None
    
    async def authenticate_session(self, session: Session) -> None:
        """Authenticate a session using Firebase"""
        try:
            session.status = SessionStatus.AUTHENTICATING
            log_session_event("authenticating", session.id, email=session.account.email)
            
            # Authenticate with Firebase
            auth_result = await self.authenticator.authenticate(
                session.account.email,
                session.account.password
            )
            
            # Update session with auth data
            session.mark_authenticated(
                firebase_token=auth_result["token"],
                cookies=auth_result.get("cookies", {})
            )
            
            log_session_event(
                "authenticated", 
                session.id,
                expires_at=session.expires_at.isoformat() if session.expires_at else None
            )
            
        except Exception as e:
            session.mark_error()
            log_session_event("auth_failed", session.id, error=str(e))
            raise AuthenticationError(f"Failed to authenticate session: {str(e)}")
    
    async def get_active_session(self) -> Session:
        """Get an active session from the pool"""
        session = self.pool_manager.get_active_session()
        
        if not session:
            # Try to create a new session if pool is not full
            if len(self.pool_manager.pool.sessions) < settings.max_concurrent_sessions:
                session = await self._create_emergency_session()
            
            if not session:
                raise SessionPoolExhaustedError("No active sessions available")
        
        # Check if session needs refresh
        if session.time_until_expiry() and session.time_until_expiry().total_seconds() < 300:  # 5 minutes
            try:
                await self.refresh_session(session)
            except Exception as e:
                self.logger.warning(
                    "Failed to refresh session, will try another",
                    session_id=session.id,
                    error=str(e)
                )
                # Mark as expired and try to get another session
                session.mark_expired()
                return await self.get_active_session()
        
        session.update_last_used()
        return session
    
    async def _create_emergency_session(self) -> Optional[Session]:
        """Create an emergency session when pool is low"""
        # Find an account that doesn't have an active session
        used_emails = {s.account.email for s in self.pool_manager.pool.sessions if s.is_active()}
        available_accounts = [acc for acc in self.accounts if acc.email not in used_emails]
        
        if not available_accounts:
            return None
        
        # Use the first available account
        account = available_accounts[0]
        return await self._create_session_for_account(account)
    
    async def refresh_session(self, session: Session) -> None:
        """Refresh an expired or expiring session"""
        try:
            log_session_event("refreshing", session.id)
            
            # Re-authenticate the session
            await self.authenticate_session(session)
            
            log_session_event("refreshed", session.id)
            
        except Exception as e:
            session.mark_error()
            log_session_event("refresh_failed", session.id, error=str(e))
            raise SessionExpiredError(f"Failed to refresh session: {str(e)}")
    
    async def maintain_presence(self, session: Session) -> None:
        """Maintain presence for a session (keep-alive)"""
        try:
            # This would typically involve making a lightweight API call
            # to keep the session active
            log_session_event("presence_maintained", session.id)
            
        except Exception as e:
            self.logger.warning(
                "Failed to maintain presence",
                session_id=session.id,
                error=str(e)
            )
    
    async def handle_session_expiry(self, session: Session) -> Session:
        """Handle session expiry by refreshing or creating new session"""
        try:
            await self.refresh_session(session)
            return session
        except Exception:
            # Remove expired session and create new one
            self.pool_manager.remove_session(session.id)
            
            # Create new session with same account
            new_session = await self._create_session_for_account(session.account)
            if new_session:
                return new_session
            
            raise SessionError("Failed to handle session expiry")
    
    @asynccontextmanager
    async def get_session_context(self):
        """Context manager for getting and releasing sessions"""
        session = await self.get_active_session()
        try:
            yield session
        finally:
            # Session is automatically returned to pool
            pass
    
    async def _cleanup_loop(self) -> None:
        """Background task to cleanup expired sessions"""
        while self._is_running:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Cleanup expired sessions
                removed_count = self.pool_manager.cleanup_expired_sessions()
                if removed_count > 0:
                    self.logger.info(f"Cleaned up {removed_count} expired sessions")
                
                # Maintain presence for active sessions
                active_sessions = [s for s in self.pool_manager.pool.sessions if s.is_active()]
                for session in active_sessions:
                    try:
                        await self.maintain_presence(session)
                    except Exception as e:
                        self.logger.warning(
                            "Failed to maintain presence for session",
                            session_id=session.id,
                            error=str(e)
                        )
                
                # Log pool stats
                stats = self.pool_manager.get_stats()
                self.logger.debug("Session pool stats", **stats)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Error in cleanup loop", error=str(e))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session manager statistics"""
        pool_stats = self.pool_manager.get_stats()
        
        return {
            "is_running": self._is_running,
            "configured_accounts": len(self.accounts),
            "pool_stats": pool_stats,
            "max_sessions": settings.max_concurrent_sessions
        }
    
    async def create_session_pool(self, accounts: List[Account]) -> SessionPool:
        """Create a session pool for specific accounts"""
        pool = SessionPool(max_sessions=len(accounts))
        
        tasks = []
        for account in accounts:
            session_id = str(uuid.uuid4())
            session = Session(id=session_id, account=account)
            task = asyncio.create_task(self.authenticate_session(session))
            tasks.append((session, task))
        
        # Wait for all authentications
        for session, task in tasks:
            try:
                await task
                pool.add_session(session)
            except Exception as e:
                self.logger.error(
                    "Failed to authenticate session for pool",
                    session_id=session.id,
                    error=str(e)
                )
        
        return pool
