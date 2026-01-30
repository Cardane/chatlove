"""
Session Pool Manager for Lovable Automation Service
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..core.logging import LoggerMixin, log_session_event
from ..models.session import Session, SessionPool, SessionStatus


class SessionPoolManager(LoggerMixin):
    """
    Manages a pool of Lovable sessions with load balancing
    and health monitoring
    """
    
    def __init__(self, max_sessions: int = 5):
        self.pool = SessionPool(max_sessions=max_sessions)
        self._lock = asyncio.Lock()
    
    def add_session(self, session: Session) -> None:
        """Add a session to the pool"""
        try:
            self.pool.add_session(session)
            log_session_event("added_to_pool", session.id, pool_size=len(self.pool.sessions))
        except ValueError as e:
            self.logger.warning(f"Failed to add session to pool: {str(e)}")
    
    def get_active_session(self) -> Optional[Session]:
        """Get an active session using round-robin load balancing"""
        session = self.pool.get_active_session()
        
        if session:
            log_session_event(
                "session_assigned", 
                session.id,
                message_count=session.message_count,
                last_used=session.last_used_at.isoformat() if session.last_used_at else None
            )
        
        return session
    
    def get_least_used_session(self) -> Optional[Session]:
        """Get the session with the lowest message count"""
        session = self.pool.get_least_used_session()
        
        if session:
            log_session_event(
                "least_used_assigned",
                session.id,
                message_count=session.message_count
            )
        
        return session
    
    def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """Get a specific session by ID"""
        return self.pool.get_session_by_id(session_id)
    
    def get_session_by_account(self, email: str) -> Optional[Session]:
        """Get session by account email"""
        return self.pool.get_session_by_account(email)
    
    def remove_session(self, session_id: str) -> bool:
        """Remove a session from the pool"""
        removed = self.pool.remove_session(session_id)
        
        if removed:
            log_session_event("removed_from_pool", session_id, pool_size=len(self.pool.sessions))
        
        return removed
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions and return count"""
        initial_count = len(self.pool.sessions)
        removed_count = self.pool.cleanup_expired_sessions()
        
        if removed_count > 0:
            self.logger.info(
                f"Cleaned up {removed_count} expired sessions",
                initial_count=initial_count,
                final_count=len(self.pool.sessions)
            )
        
        return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get detailed pool statistics"""
        stats = self.pool.get_stats()
        
        # Add additional statistics
        sessions = self.pool.sessions
        
        if sessions:
            # Message count statistics
            message_counts = [s.message_count for s in sessions]
            stats.update({
                "avg_messages_per_session": sum(message_counts) / len(message_counts),
                "max_messages_per_session": max(message_counts),
                "min_messages_per_session": min(message_counts),
                "total_messages_processed": sum(message_counts)
            })
            
            # Error statistics
            error_counts = [s.error_count for s in sessions]
            stats.update({
                "total_errors": sum(error_counts),
                "avg_errors_per_session": sum(error_counts) / len(error_counts),
                "max_errors_per_session": max(error_counts)
            })
            
            # Session age statistics
            now = datetime.utcnow()
            ages = [(now - s.created_at).total_seconds() for s in sessions]
            stats.update({
                "avg_session_age_seconds": sum(ages) / len(ages),
                "oldest_session_age_seconds": max(ages),
                "newest_session_age_seconds": min(ages)
            })
        
        return stats
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get detailed health report of all sessions"""
        sessions_health = []
        
        for session in self.pool.sessions:
            health_info = {
                "session_id": session.id,
                "account_email": session.account.email,
                "status": session.status,
                "is_active": session.is_active(),
                "is_expired": session.is_expired(),
                "message_count": session.message_count,
                "error_count": session.error_count,
                "created_at": session.created_at.isoformat(),
                "authenticated_at": session.authenticated_at.isoformat() if session.authenticated_at else None,
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                "last_used_at": session.last_used_at.isoformat() if session.last_used_at else None,
                "time_until_expiry": session.time_until_expiry().total_seconds() if session.time_until_expiry() else None
            }
            sessions_health.append(health_info)
        
        # Overall health metrics
        active_count = len([s for s in self.pool.sessions if s.is_active()])
        error_count = len([s for s in self.pool.sessions if s.status == SessionStatus.ERROR])
        expired_count = len([s for s in self.pool.sessions if s.is_expired()])
        
        health_score = 0.0
        if self.pool.sessions:
            health_score = active_count / len(self.pool.sessions)
        
        return {
            "overall_health": {
                "health_score": health_score,
                "total_sessions": len(self.pool.sessions),
                "active_sessions": active_count,
                "error_sessions": error_count,
                "expired_sessions": expired_count,
                "pool_utilization": len(self.pool.sessions) / self.pool.max_sessions
            },
            "sessions": sessions_health
        }
    
    async def health_check_session(self, session: Session) -> bool:
        """Perform health check on a specific session"""
        try:
            # Basic checks
            if not session.is_active():
                return False
            
            if session.is_expired():
                return False
            
            # Check if session has too many errors
            if session.error_count > 5:
                self.logger.warning(
                    "Session has too many errors",
                    session_id=session.id,
                    error_count=session.error_count
                )
                return False
            
            # Additional health checks could be added here
            # For example, making a test API call
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Error during session health check",
                session_id=session.id,
                error=str(e)
            )
            return False
    
    async def perform_health_checks(self) -> Dict[str, Any]:
        """Perform health checks on all sessions"""
        results = {
            "healthy_sessions": [],
            "unhealthy_sessions": [],
            "total_checked": 0,
            "healthy_count": 0,
            "unhealthy_count": 0
        }
        
        for session in self.pool.sessions:
            results["total_checked"] += 1
            
            is_healthy = await self.health_check_session(session)
            
            session_info = {
                "session_id": session.id,
                "account_email": session.account.email,
                "status": session.status,
                "message_count": session.message_count,
                "error_count": session.error_count
            }
            
            if is_healthy:
                results["healthy_sessions"].append(session_info)
                results["healthy_count"] += 1
            else:
                results["unhealthy_sessions"].append(session_info)
                results["unhealthy_count"] += 1
        
        return results
    
    async def close_all_sessions(self) -> None:
        """Close all sessions in the pool"""
        async with self._lock:
            session_count = len(self.pool.sessions)
            
            # Mark all sessions as inactive
            for session in self.pool.sessions:
                session.status = SessionStatus.INACTIVE
                log_session_event("closed", session.id)
            
            # Clear the pool
            self.pool.sessions.clear()
            
            self.logger.info(f"Closed {session_count} sessions")
    
    def rebalance_load(self) -> None:
        """Rebalance load across sessions by resetting round-robin index"""
        # Find the session with the lowest message count
        if self.pool.sessions:
            least_used = min(self.pool.sessions, key=lambda s: s.message_count if s.is_active() else float('inf'))
            
            # Find its index in active sessions
            active_sessions = [s for s in self.pool.sessions if s.is_active()]
            if least_used in active_sessions:
                self.pool.current_index = active_sessions.index(least_used)
                
                self.logger.info(
                    "Load rebalanced",
                    new_index=self.pool.current_index,
                    target_session=least_used.id,
                    message_count=least_used.message_count
                )
    
    def get_session_distribution(self) -> Dict[str, Any]:
        """Get distribution of messages across sessions"""
        if not self.pool.sessions:
            return {"sessions": [], "distribution": "empty"}
        
        session_loads = []
        for session in self.pool.sessions:
            session_loads.append({
                "session_id": session.id,
                "account_email": session.account.email,
                "message_count": session.message_count,
                "error_count": session.error_count,
                "status": session.status,
                "load_percentage": 0.0
            })
        
        # Calculate load percentages
        total_messages = sum(s["message_count"] for s in session_loads)
        if total_messages > 0:
            for session_load in session_loads:
                session_load["load_percentage"] = (session_load["message_count"] / total_messages) * 100
        
        # Determine distribution quality
        if len(session_loads) <= 1:
            distribution = "single"
        else:
            load_percentages = [s["load_percentage"] for s in session_loads]
            std_dev = (sum((x - (100/len(session_loads)))**2 for x in load_percentages) / len(load_percentages))**0.5
            
            if std_dev < 10:
                distribution = "balanced"
            elif std_dev < 25:
                distribution = "moderate"
            else:
                distribution = "unbalanced"
        
        return {
            "sessions": session_loads,
            "distribution": distribution,
            "total_messages": total_messages,
            "active_sessions": len([s for s in session_loads if s["status"] == "active"])
        }
