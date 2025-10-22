"""
Agent Runtime Service for RiskIntel360 Platform
Handles agent session management, state persistence, and lifecycle management.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import weakref

from riskintel360.config.settings import get_settings
from riskintel360.models.agent_models import AgentSession, AgentState, SessionStatus

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Agent session status enumeration"""
    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


@dataclass
class AgentSession:
    """Agent session data model"""
    session_id: str
    agent_type: str
    user_id: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    state_data: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "agent_type": self.agent_type,
            "user_id": self.user_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "state_data": self.state_data,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentSession":
        """Create session from dictionary"""
        return cls(
            session_id=data["session_id"],
            agent_type=data["agent_type"],
            user_id=data["user_id"],
            status=SessionStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            state_data=data["state_data"],
            metadata=data["metadata"],
        )


class AgentSessionManager:
    """
    Manages agent sessions with asyncio and state persistence.
    Handles session lifecycle, state management, and cleanup.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._sessions: Dict[str, AgentSession] = {}
        self._session_locks: Dict[str, asyncio.Lock] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Session limits
        self.max_sessions = self.settings.agents.max_concurrent_agents
        self.session_timeout = self.settings.agents.workflow_timeout_seconds
        
        # Weak reference to track active tasks
        self._active_tasks: Set[asyncio.Task] = set()
        
    async def start(self) -> None:
        """Start the session manager"""
        if self._running:
            return
            
        self._running = True
        logger.info("Starting Agent Session Manager")
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
        
        # Load existing sessions from persistence
        await self._load_sessions()
        
    async def stop(self) -> None:
        """Stop the session manager and cleanup resources"""
        if not self._running:
            return
            
        self._running = False
        logger.info("Stopping Agent Session Manager")
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all active tasks
        for task in self._active_tasks.copy():
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
        
        # Save all sessions before shutdown
        await self._save_all_sessions()
        
    async def create_session(
        self,
        agent_type: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentSession:
        """Create a new agent session"""
        
        # Check session limits
        active_sessions = len([s for s in self._sessions.values() 
                             if s.status in [SessionStatus.RUNNING, SessionStatus.INITIALIZING]])
        
        if active_sessions >= self.max_sessions:
            raise RuntimeError(f"Maximum concurrent sessions ({self.max_sessions}) reached")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create session
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.session_timeout)
        
        session = AgentSession(
            session_id=session_id,
            agent_type=agent_type,
            user_id=user_id,
            status=SessionStatus.CREATED,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            state_data={},
            metadata=metadata or {},
        )
        
        # Store session
        self._sessions[session_id] = session
        self._session_locks[session_id] = asyncio.Lock()
        
        # Persist session
        await self._save_session(session)
        
        logger.info(f"Created agent session {session_id} for agent type {agent_type}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Get an agent session by ID"""
        return self._sessions.get(session_id)
    
    async def update_session_status(
        self,
        session_id: str,
        status: SessionStatus,
        state_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update session status and optionally state data"""
        
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        async with self._session_locks[session_id]:
            session.status = status
            session.updated_at = datetime.now(timezone.utc)
            
            if state_data is not None:
                session.state_data.update(state_data)
            
            # Persist changes
            await self._save_session(session)
            
        logger.debug(f"Updated session {session_id} status to {status.value}")
        return True
    
    async def update_session_state(
        self,
        session_id: str,
        state_data: Dict[str, Any]
    ) -> bool:
        """Update session state data"""
        
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        async with self._session_locks[session_id]:
            session.state_data.update(state_data)
            session.updated_at = datetime.now(timezone.utc)
            
            # Persist changes
            await self._save_session(session)
            
        logger.debug(f"Updated session {session_id} state data")
        return True
    
    async def terminate_session(self, session_id: str) -> bool:
        """Terminate an agent session"""
        
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        async with self._session_locks[session_id]:
            session.status = SessionStatus.TERMINATED
            session.updated_at = datetime.now(timezone.utc)
            
            # Persist changes
            await self._save_session(session)
        
        logger.info(f"Terminated agent session {session_id}")
        return True
    
    async def cleanup_session(self, session_id: str) -> bool:
        """Clean up and remove a session"""
        
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        # Remove from memory
        del self._sessions[session_id]
        if session_id in self._session_locks:
            del self._session_locks[session_id]
        
        # Remove from persistence
        await self._delete_session(session_id)
        
        logger.info(f"Cleaned up agent session {session_id}")
        return True
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        status: Optional[SessionStatus] = None
    ) -> List[AgentSession]:
        """List sessions with optional filtering"""
        
        sessions = list(self._sessions.values())
        
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        
        if agent_type:
            sessions = [s for s in sessions if s.agent_type == agent_type]
        
        if status:
            sessions = [s for s in sessions if s.status == status]
        
        return sessions
    
    async def get_session_count(self) -> Dict[str, int]:
        """Get session count by status"""
        counts = {}
        for status in SessionStatus:
            counts[status.value] = len([s for s in self._sessions.values() if s.status == status])
        return counts
    
    async def extend_session(self, session_id: str, extension_seconds: int = 3600) -> bool:
        """Extend session expiration time"""
        
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        async with self._session_locks[session_id]:
            session.expires_at += timedelta(seconds=extension_seconds)
            session.updated_at = datetime.now(timezone.utc)
            
            # Persist changes
            await self._save_session(session)
        
        logger.info(f"Extended session {session_id} by {extension_seconds} seconds")
        return True
    
    async def _cleanup_expired_sessions(self) -> None:
        """Background task to cleanup expired sessions"""
        
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                expired_sessions = []
                
                for session in self._sessions.values():
                    if session.expires_at < now:
                        expired_sessions.append(session.session_id)
                
                # Cleanup expired sessions
                for session_id in expired_sessions:
                    await self.cleanup_session(session_id)
                
                # Sleep for cleanup interval
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
                await asyncio.sleep(60)
    
    async def _save_session(self, session: AgentSession) -> None:
        """Save session to persistence layer"""
        # In a real implementation, this would save to Redis/DynamoDB
        # For now, we'll use in-memory storage with file backup
        try:
            # This is a placeholder - in production, use Redis or DynamoDB
            logger.debug(f"Persisting session {session.session_id}")
        except Exception as e:
            logger.error(f"Failed to persist session {session.session_id}: {e}")
    
    async def _load_sessions(self) -> None:
        """Load sessions from persistence layer"""
        try:
            # This is a placeholder - in production, load from Redis or DynamoDB
            logger.info("Loading existing sessions from persistence")
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
    
    async def _save_all_sessions(self) -> None:
        """Save all sessions to persistence"""
        for session in self._sessions.values():
            await self._save_session(session)
    
    async def _delete_session(self, session_id: str) -> None:
        """Delete session from persistence layer"""
        try:
            # This is a placeholder - in production, delete from Redis or DynamoDB
            logger.debug(f"Deleting session {session_id} from persistence")
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")


# Global session manager instance
_session_manager: Optional[AgentSessionManager] = None


async def get_session_manager() -> AgentSessionManager:
    """Get the global session manager instance"""
    global _session_manager
    
    if _session_manager is None:
        _session_manager = AgentSessionManager()
        await _session_manager.start()
    
    return _session_manager


async def shutdown_session_manager() -> None:
    """Shutdown the global session manager"""
    global _session_manager
    
    if _session_manager:
        await _session_manager.stop()
        _session_manager = None
