"""
Session Manager for Label Maker Application
Ensures database changes are immediately available to all users while maintaining session isolation.
"""

import threading
import time
import logging
import hashlib
from typing import Dict, Set, Optional, Any, List
from datetime import datetime, timedelta
from flask import session, g, current_app
from dataclasses import dataclass
from collections import defaultdict
import queue

logger = logging.getLogger(__name__)

@dataclass
class DatabaseChange:
    """Represents a database change that needs to be propagated to all sessions."""
    change_type: str  # 'lineage_update', 'product_add', 'strain_update', etc.
    entity_id: str    # ID of the changed entity
    entity_type: str  # 'strain', 'product', etc.
    timestamp: datetime
    user_id: Optional[str] = None  # User who made the change
    details: Optional[Dict[str, Any]] = None

class SessionManager:
    """
    Manages user sessions and ensures database changes are immediately available
    to all users while maintaining session isolation.
    """
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._session_locks: Dict[str, threading.Lock] = {}
        self._database_changes: List[DatabaseChange] = []
        self._change_notifications: Dict[str, Set[str]] = defaultdict(set)  # session_id -> set of change_ids
        self._global_lock = threading.RLock()  # Use RLock for better performance
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes
        
        # Add a queue for non-blocking operations
        self._operation_queue = queue.Queue(maxsize=1000)
        self._queue_thread = threading.Thread(target=self._process_operation_queue, daemon=True)
        self._queue_thread.start()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_old_sessions, daemon=True)
        self._cleanup_thread.start()
    
    def _process_operation_queue(self):
        """Process operations from the queue in a separate thread."""
        while True:
            try:
                operation = self._operation_queue.get(timeout=1.0)
                if operation is None:  # Shutdown signal
                    break
                
                operation_type, args, kwargs = operation
                if operation_type == 'record_change':
                    self._record_change_sync(*args, **kwargs)
                elif operation_type == 'update_session':
                    self._update_session_sync(*args, **kwargs)
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing operation queue: {e}")
    
    def _record_change_sync(self, change: DatabaseChange):
        """Synchronous version of record_database_change."""
        try:
            with self._global_lock:
                self._database_changes.append(change)
                
                # Mark all active sessions as needing notification
                for session_id in self._sessions.keys():
                    self._change_notifications[session_id].add(change.entity_id)
                
                # Keep only recent changes (last 100)
                if len(self._database_changes) > 100:
                    self._database_changes = self._database_changes[-100:]
                
                logger.info(f"Recorded database change: {change.change_type} for {change.entity_type} {change.entity_id}")
        except Exception as e:
            logger.error(f"Error recording database change: {e}")
    
    def _update_session_sync(self, session_id: str, key: str, value: Any):
        """Synchronous version of set_session_data."""
        try:
            with self._global_lock:
                if session_id in self._sessions:
                    self._sessions[session_id][key] = value
                    self._sessions[session_id]['last_activity'] = datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Error updating session data: {e}")
    
    def get_session_id(self) -> str:
        """Get or create a unique session ID for the current request."""
        try:
            # Try to get session from Flask context
            if 'session_id' not in session:
                # Create a unique session ID based on user agent and timestamp
                user_agent = session.get('user_agent', 'unknown')
                timestamp = str(time.time())
                session_hash = hashlib.md5(f"{user_agent}:{timestamp}".encode()).hexdigest()
                session['session_id'] = session_hash
                session['created_at'] = datetime.now().isoformat()
                session['last_activity'] = datetime.now().isoformat()
                
                # Initialize session in manager (non-blocking)
                try:
                    with self._global_lock:
                        self._sessions[session_hash] = {
                            'created_at': session['created_at'],
                            'last_activity': session['last_activity'],
                            'user_agent': user_agent,
                            'selected_tags': [],
                            'filters': {},
                            'database_version': 0
                        }
                        self._session_locks[session_hash] = threading.Lock()
                except Exception as e:
                    logger.error(f"Error initializing session: {e}")
            
            # Update last activity (non-blocking)
            session['last_activity'] = datetime.now().isoformat()
            session_id = session['session_id']
            
            # Queue the update operation
            try:
                self._operation_queue.put_nowait(('update_session', (session_id, 'last_activity', session['last_activity']), {}))
            except queue.Full:
                logger.warning("Operation queue full, skipping session update")
            
            return session_id
            
        except RuntimeError:
            # Working outside of request context (e.g., in tests)
            # Create a test session ID
            thread_id = threading.get_ident()
            timestamp = str(time.time())
            test_session_hash = hashlib.md5(f"test:{thread_id}:{timestamp}".encode()).hexdigest()
            
            # Initialize test session in manager
            try:
                with self._global_lock:
                    if test_session_hash not in self._sessions:
                        self._sessions[test_session_hash] = {
                            'created_at': datetime.now().isoformat(),
                            'last_activity': datetime.now().isoformat(),
                            'user_agent': 'test',
                            'selected_tags': [],
                            'filters': {},
                            'database_version': 0
                        }
                        self._session_locks[test_session_hash] = threading.Lock()
            except Exception as e:
                logger.error(f"Error initializing test session: {e}")
            
            return test_session_hash
    
    def get_session_data(self, key: str, default: Any = None) -> Any:
        """Get session data for the current session."""
        try:
            session_id = self.get_session_id()
            with self._global_lock:
                if session_id in self._sessions:
                    return self._sessions[session_id].get(key, default)
        except Exception as e:
            logger.error(f"Error getting session data: {e}")
        return default
    
    def set_session_data(self, key: str, value: Any) -> None:
        """Set session data for the current session (non-blocking)."""
        try:
            session_id = self.get_session_id()
            # Queue the update operation instead of doing it synchronously
            self._operation_queue.put_nowait(('update_session', (session_id, key, value), {}))
        except queue.Full:
            logger.warning("Operation queue full, skipping session data update")
        except Exception as e:
            logger.error(f"Error setting session data: {e}")
    
    def record_database_change(self, change: DatabaseChange) -> None:
        """Record a database change that needs to be propagated to all sessions (non-blocking)."""
        try:
            # Queue the operation instead of doing it synchronously
            self._operation_queue.put_nowait(('record_change', (change,), {}))
        except queue.Full:
            logger.warning("Operation queue full, skipping database change recording")
        except Exception as e:
            logger.error(f"Error recording database change: {e}")
    
    def get_pending_changes(self, session_id: str) -> List[DatabaseChange]:
        """Get pending database changes for a specific session."""
        try:
            with self._global_lock:
                if session_id not in self._change_notifications:
                    return []
                
                pending_change_ids = self._change_notifications[session_id]
                pending_changes = [
                    change for change in self._database_changes
                    if change.entity_id in pending_change_ids
                ]
                
                # Clear notifications for this session
                self._change_notifications[session_id].clear()
                
                return pending_changes
        except Exception as e:
            logger.error(f"Error getting pending changes: {e}")
            return []
    
    def has_pending_changes(self, session_id: str) -> bool:
        """Check if a session has pending database changes."""
        try:
            with self._global_lock:
                return bool(self._change_notifications.get(session_id, set()))
        except Exception as e:
            logger.error(f"Error checking pending changes: {e}")
            return False
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions."""
        try:
            with self._global_lock:
                active_sessions = len(self._sessions)
                total_changes = len(self._database_changes)
                pending_notifications = sum(len(notifications) for notifications in self._change_notifications.values())
                
                return {
                    'active_sessions': active_sessions,
                    'total_database_changes': total_changes,
                    'pending_notifications': pending_notifications,
                    'last_cleanup': datetime.fromtimestamp(self._last_cleanup).isoformat(),
                    'queue_size': self._operation_queue.qsize()
                }
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {}
    
    def _cleanup_old_sessions(self) -> None:
        """Clean up old sessions and database changes."""
        while True:
            try:
                time.sleep(60)  # Check every minute
                current_time = time.time()
                
                if current_time - self._last_cleanup < self._cleanup_interval:
                    continue
                
                with self._global_lock:
                    # Remove sessions older than 2 hours
                    cutoff_time = datetime.now() - timedelta(hours=2)
                    sessions_to_remove = []
                    
                    for session_id, session_data in self._sessions.items():
                        last_activity = datetime.fromisoformat(session_data['last_activity'])
                        if last_activity < cutoff_time:
                            sessions_to_remove.append(session_id)
                    
                    for session_id in sessions_to_remove:
                        del self._sessions[session_id]
                        if session_id in self._session_locks:
                            del self._session_locks[session_id]
                        if session_id in self._change_notifications:
                            del self._change_notifications[session_id]
                    
                    # Remove database changes older than 1 hour
                    cutoff_time = datetime.now() - timedelta(hours=1)
                    self._database_changes = [
                        change for change in self._database_changes
                        if change.timestamp > cutoff_time
                    ]
                    
                    self._last_cleanup = current_time
                    
                    if sessions_to_remove:
                        logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")
                        
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
    
    def clear_session(self, session_id: str) -> None:
        """Clear a specific session."""
        try:
            with self._global_lock:
                if session_id in self._sessions:
                    del self._sessions[session_id]
                if session_id in self._session_locks:
                    del self._session_locks[session_id]
                if session_id in self._change_notifications:
                    del self._change_notifications[session_id]
        except Exception as e:
            logger.error(f"Error clearing session: {e}")

# Global session manager instance
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

def get_current_session_id() -> str:
    """Get the current session ID."""
    return get_session_manager().get_session_id()

def get_session_data(key: str, default: Any = None) -> Any:
    """Get session data for the current session."""
    return get_session_manager().get_session_data(key, default)

def set_session_data(key: str, value: Any) -> None:
    """Set session data for the current session."""
    get_session_manager().set_session_data(key, value)

def record_database_change(change_type: str, entity_id: str, entity_type: str, 
                          user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
    """Record a database change that needs to be propagated to all sessions."""
    change = DatabaseChange(
        change_type=change_type,
        entity_id=entity_id,
        entity_type=entity_type,
        timestamp=datetime.now(),
        user_id=user_id,
        details=details
    )
    get_session_manager().record_database_change(change)

def get_pending_changes() -> List[DatabaseChange]:
    """Get pending database changes for the current session."""
    session_id = get_current_session_id()
    return get_session_manager().get_pending_changes(session_id)

def has_pending_changes() -> bool:
    """Check if the current session has pending database changes."""
    session_id = get_current_session_id()
    return get_session_manager().has_pending_changes(session_id) 