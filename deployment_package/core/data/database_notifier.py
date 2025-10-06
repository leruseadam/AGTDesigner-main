"""
Database Notifier for Label Maker Application
Integrates with session manager to ensure immediate propagation of database changes.
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from .session_manager import record_database_change, get_session_manager

logger = logging.getLogger(__name__)

class DatabaseNotifier:
    """
    Notifies all sessions of database changes to ensure immediate availability
    of changes across all browsers while maintaining session isolation.
    """
    
    def __init__(self):
        self._change_handlers: Dict[str, Callable] = {}
        self._lock = threading.RLock()  # Use RLock for better performance
        self._notification_timeout = 5.0  # 5 second timeout for notifications
    
    def register_change_handler(self, change_type: str, handler: Callable) -> None:
        """Register a handler for a specific type of database change."""
        with self._lock:
            self._change_handlers[change_type] = handler
            logger.info(f"Registered change handler for: {change_type}")
    
    def _notify_with_timeout(self, change_type: str, *args, **kwargs):
        """Notify with timeout protection."""
        try:
            with self._lock:
                if change_type in self._change_handlers:
                    # Run handler in a separate thread with timeout
                    def run_handler():
                        try:
                            self._change_handlers[change_type](*args, **kwargs)
                        except Exception as e:
                            logger.error(f"Error in {change_type} handler: {e}")
                    
                    thread = threading.Thread(target=run_handler, daemon=True)
                    thread.start()
                    thread.join(timeout=self._notification_timeout)
                    
                    if thread.is_alive():
                        logger.warning(f"{change_type} handler timed out after {self._notification_timeout}s")
        except Exception as e:
            logger.error(f"Error in notification timeout protection: {e}")
    
    def notify_lineage_update(self, strain_name: str, old_lineage: str, new_lineage: str, 
                            user_id: Optional[str] = None) -> None:
        """Notify all sessions of a lineage update."""
        try:
            # Record the change for all sessions (non-blocking)
            record_database_change(
                change_type='lineage_update',
                entity_id=strain_name,
                entity_type='strain',
                user_id=user_id,
                details={
                    'old_lineage': old_lineage,
                    'new_lineage': new_lineage,
                    'strain_name': strain_name
                }
            )
            
            # Call any registered handlers with timeout protection
            self._notify_with_timeout('lineage_update', strain_name, old_lineage, new_lineage)
            
            logger.info(f"Notified all sessions of lineage update: {strain_name} {old_lineage} -> {new_lineage}")
            
        except Exception as e:
            logger.error(f"Error notifying lineage update: {e}")
    
    def notify_product_update(self, product_name: str, product_data: Dict[str, Any], 
                            user_id: Optional[str] = None) -> None:
        """Notify all sessions of a product update."""
        try:
            record_database_change(
                change_type='product_update',
                entity_id=product_name,
                entity_type='product',
                user_id=user_id,
                details=product_data
            )
            
            self._notify_with_timeout('product_update', product_name, product_data)
            
            logger.info(f"Notified all sessions of product update: {product_name}")
            
        except Exception as e:
            logger.error(f"Error notifying product update: {e}")
    
    def notify_strain_add(self, strain_name: str, strain_data: Dict[str, Any], 
                         user_id: Optional[str] = None) -> None:
        """Notify all sessions of a new strain being added."""
        try:
            record_database_change(
                change_type='strain_add',
                entity_id=strain_name,
                entity_type='strain',
                user_id=user_id,
                details=strain_data
            )
            
            self._notify_with_timeout('strain_add', strain_name, strain_data)
            
            logger.info(f"Notified all sessions of new strain: {strain_name}")
            
        except Exception as e:
            logger.error(f"Error notifying strain add: {e}")
    
    def notify_sovereign_lineage_set(self, strain_name: str, sovereign_lineage: str, 
                                   user_id: Optional[str] = None) -> None:
        """Notify all sessions of a sovereign lineage being set."""
        try:
            record_database_change(
                change_type='sovereign_lineage_set',
                entity_id=strain_name,
                entity_type='strain',
                user_id=user_id,
                details={
                    'sovereign_lineage': sovereign_lineage,
                    'strain_name': strain_name
                }
            )
            
            self._notify_with_timeout('sovereign_lineage_set', strain_name, sovereign_lineage)
            
            logger.info(f"Notified all sessions of sovereign lineage set: {strain_name} -> {sovereign_lineage}")
            
        except Exception as e:
            logger.error(f"Error notifying sovereign lineage set: {e}")
    
    def notify_database_refresh(self, reason: str, user_id: Optional[str] = None) -> None:
        """Notify all sessions that the database has been refreshed."""
        try:
            record_database_change(
                change_type='database_refresh',
                entity_id='database',
                entity_type='system',
                user_id=user_id,
                details={'reason': reason}
            )
            
            self._notify_with_timeout('database_refresh', reason)
            
            logger.info(f"Notified all sessions of database refresh: {reason}")
            
        except Exception as e:
            logger.error(f"Error notifying database refresh: {e}")

# Global database notifier instance
_database_notifier = None

def get_database_notifier() -> DatabaseNotifier:
    """Get the global database notifier instance."""
    global _database_notifier
    if _database_notifier is None:
        _database_notifier = DatabaseNotifier()
    return _database_notifier

def notify_lineage_update(strain_name: str, old_lineage: str, new_lineage: str, 
                         user_id: Optional[str] = None) -> None:
    """Notify all sessions of a lineage update."""
    get_database_notifier().notify_lineage_update(strain_name, old_lineage, new_lineage, user_id)

def notify_product_update(product_name: str, product_data: Dict[str, Any], 
                         user_id: Optional[str] = None) -> None:
    """Notify all sessions of a product update."""
    get_database_notifier().notify_product_update(product_name, product_data, user_id)

def notify_strain_add(strain_name: str, strain_data: Dict[str, Any], 
                     user_id: Optional[str] = None) -> None:
    """Notify all sessions of a new strain being added."""
    get_database_notifier().notify_strain_add(strain_name, strain_data, user_id)

def notify_sovereign_lineage_set(strain_name: str, sovereign_lineage: str, 
                               user_id: Optional[str] = None) -> None:
    """Notify all sessions of a sovereign lineage being set."""
    get_database_notifier().notify_sovereign_lineage_set(strain_name, sovereign_lineage, user_id)

def notify_database_refresh(reason: str, user_id: Optional[str] = None) -> None:
    """Notify all sessions that the database has been refreshed."""
    get_database_notifier().notify_database_refresh(reason, user_id) 