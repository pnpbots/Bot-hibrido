#!/usr/bin/env python3
"""
Enhanced Database Module for PNP Television Bot
Combines robust error handling with comprehensive database functionality.
"""

import logging
import sqlite3
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
from dataclasses import dataclass

from app.config import app_config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database Connection Management
# ---------------------------------------------------------------------------

class DatabaseManager:
    """Enhanced database manager with connection pooling and error handling."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or app_config.database.url.replace("sqlite:///", "")
        self.lock = threading.Lock()
        self._ensure_db_directory()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists."""
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = (), fetch: bool = False) -> Any:
        """Execute query with comprehensive error handling."""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    
                    if fetch:
                        if "SELECT" in query.upper():
                            return cursor.fetchall()
                        return cursor.fetchone()
                    else:
                        conn.commit()
                        return cursor.rowcount
                        
            except sqlite3.IntegrityError as e:
                logger.warning(f"Database integrity error: {e}")
                raise
            except sqlite3.OperationalError as e:
                logger.error(f"Database operational error: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected database error: {e}")
                raise
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute multiple queries in a transaction."""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.executemany(query, params_list)
                    conn.commit()
                    return cursor.rowcount
            except Exception as e:
                logger.error(f"Batch execution error: {e}")
                raise

# Global database manager
db_manager = DatabaseManager()

# ---------------------------------------------------------------------------
# Table Creation and Schema Management
# ---------------------------------------------------------------------------

def create_tables():
    """Create all required tables with enhanced error handling."""
    logger.info("Creating database tables...")
    
    tables = {
        'users': '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT DEFAULT 'es',
                phone_number TEXT,
                is_admin BOOLEAN DEFAULT FALSE,
                is_banned BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                notes TEXT,
                FOREIGN KEY (referred_by) REFERENCES users (telegram_id)
            )
        ''',
        
        'user_settings': '''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                setting_key TEXT NOT NULL,
                setting_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                UNIQUE(user_id, setting_key)
            )
        ''',
        
        'subscriptions': '''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                payment_amount REAL,
                payment_method TEXT,
                payment_reference TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        ''',
        
        'payments': '''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subscription_id INTEGER,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                payment_method TEXT,
                payment_reference TEXT,
                status TEXT DEFAULT 'pending',
                gateway_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                FOREIGN KEY (subscription_id) REFERENCES subscriptions (id)
            )
        ''',
        
        'bot_settings': '''
            CREATE TABLE IF NOT EXISTS bot_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        
        'audit_log': '''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                admin_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                FOREIGN KEY (admin_id) REFERENCES users (telegram_id)
            )
        ''',
        
        'analytics_events': '''
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_type TEXT NOT NULL,
                event_data TEXT,
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        '''
    }
    
    # Create tables
    for table_name, create_sql in tables.items():
        try:
            db_manager.execute_query(create_sql)
            logger.info(f"✅ Table '{table_name}' ready")
        except Exception as e:
            logger.error(f"❌ Failed to create table '{table_name}': {e}")
            raise
    
    # Create indexes for performance
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users (telegram_id)",
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)",
        "CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions (status)",
        "CREATE INDEX IF NOT EXISTS idx_subscriptions_end_date ON subscriptions (end_date)",
        "CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments (status)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log (created_at)",
        "CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON analytics_events (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics_events (event_type)"
    ]
    
    for index_sql in indexes:
        try:
            db_manager.execute_query(index_sql)
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    logger.info("✅ Database schema created successfully")

def test_database_connection() -> bool:
    """Test database connection and basic operations."""
    try:
        # Test basic query
        result = db_manager.execute_query("SELECT 1 as test", fetch=True)
        if not result or result[0] != 1:
            return False
        
        # Test table existence
        tables_query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('users', 'subscriptions', 'payments')
        """
        tables = db_manager.execute_query(tables_query, fetch=True)
        expected_tables = {'users', 'subscriptions', 'payments'}
        existing_tables = {row[0] for row in tables} if tables else set()
        
        if not expected_tables.issubset(existing_tables):
            logger.warning(f"Missing tables: {expected_tables - existing_tables}")
            return False
        
        logger.debug("Database connection test passed")
        return True
        
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

# ---------------------------------------------------------------------------
# User Management Functions
# ---------------------------------------------------------------------------

@dataclass
class User:
    """User data class for type safety."""
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: str = 'es'
    phone_number: Optional[str] = None
    is_admin: bool = False
    is_banned: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None

def create_user(user_data: User) -> bool:
    """Create a new user with comprehensive error handling."""
    try:
        query = '''
            INSERT OR REPLACE INTO users 
            (telegram_id, username, first_name, last_name, language_code, 
             phone_number, is_admin, is_banned, updated_at, last_activity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        '''
        params = (
            user_data.telegram_id,
            user_data.username,
            user_data.first_name,
            user_data.last_name,
            user_data.language_code or 'es',
            user_data.phone_number,
            user_data.is_admin,
            user_data.is_banned
        )
        
        rows_affected = db_manager.execute_query(query, params)
        
        if rows_affected > 0:
            logger.info(f"User {user_data.telegram_id} created/updated successfully")
            return True
        return False
        
    except Exception as e:
        logger.error(f"Failed to create user {user_data.telegram_id}: {e}")
        return False

def get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Get user by Telegram ID with error handling."""
    try:
        query = "SELECT * FROM users WHERE telegram_id = ?"
        result = db_manager.execute_query(query, (telegram_id,), fetch=True)
        
        if result:
            # Convert Row to dict
            user_dict = dict(result[0])
            logger.debug(f"Retrieved user {telegram_id}")
            return user_dict
        return None
        
    except Exception as e:
        logger.error(f"Failed to get user {telegram_id}: {e}")
        return None

def update_user_activity(telegram_id: int) -> bool:
    """Update user last activity timestamp."""
    try:
        query = "UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE telegram_id = ?"
        rows_affected = db_manager.execute_query(query, (telegram_id,))
        return rows_affected > 0
    except Exception as e:
        logger.error(f"Failed to update activity for user {telegram_id}: {e}")
        return False

def get_all_users(limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
    """Get all users with pagination."""
    try:
        query = "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?"
        results = db_manager.execute_query(query, (limit, offset), fetch=True)
        return [dict(row) for row in results] if results else []
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        return []

# ---------------------------------------------------------------------------
# Subscription Management Functions
# ---------------------------------------------------------------------------

def create_subscription(user_id: int, plan_type: str, start_date: datetime, 
                       end_date: datetime, payment_amount: float = None) -> Optional[int]:
    """Create a new subscription."""
    try:
        query = '''
            INSERT INTO subscriptions 
            (user_id, plan_type, status, start_date, end_date, payment_amount)
            VALUES (?, ?, 'active', ?, ?, ?)
        '''
        params = (user_id, plan_type, start_date, end_date, payment_amount)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            subscription_id = cursor.lastrowid
            
        logger.info(f"Created subscription {subscription_id} for user {user_id}")
        return subscription_id
        
    except Exception as e:
        logger.error(f"Failed to create subscription for user {user_id}: {e}")
        return None

def get_active_subscription(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user's active subscription."""
    try:
        query = '''
            SELECT * FROM subscriptions 
            WHERE user_id = ? AND status = 'active' AND end_date > CURRENT_TIMESTAMP
            ORDER BY end_date DESC LIMIT 1
        '''
        result = db_manager.execute_query(query, (user_id,), fetch=True)
        return dict(result[0]) if result else None
    except Exception as e:
        logger.error(f"Failed to get subscription for user {user_id}: {e}")
        return None

def get_expiring_subscriptions(days_ahead: int = 3) -> List[Dict[str, Any]]:
    """Get subscriptions expiring in the next N days."""
    try:
        future_date = datetime.now() + timedelta(days=days_ahead)
        query = '''
            SELECT s.*, u.telegram_id, u.username, u.first_name 
            FROM subscriptions s
            JOIN users u ON s.user_id = u.telegram_id
            WHERE s.status = 'active' 
            AND s.end_date <= ? 
            AND s.end_date > CURRENT_TIMESTAMP
        '''
        results = db_manager.execute_query(query, (future_date,), fetch=True)
        return [dict(row) for row in results] if results else []
    except Exception as e:
        logger.error(f"Failed to get expiring subscriptions: {e}")
        return []

def expire_subscriptions() -> int:
    """Mark expired subscriptions as expired."""
    try:
        query = '''
            UPDATE subscriptions 
            SET status = 'expired', updated_at = CURRENT_TIMESTAMP
            WHERE status = 'active' AND end_date <= CURRENT_TIMESTAMP
        '''
        rows_affected = db_manager.execute_query(query)
        if rows_affected > 0:
            logger.info(f"Expired {rows_affected} subscriptions")
        return rows_affected
    except Exception as e:
        logger.error(f"Failed to expire subscriptions: {e}")
        return 0

# ---------------------------------------------------------------------------
# Settings Management
# ---------------------------------------------------------------------------

def get_setting(key: str, default_value: str = None) -> Optional[str]:
    """Get bot setting value."""
    try:
        query = "SELECT setting_value FROM bot_settings WHERE setting_key = ?"
        result = db_manager.execute_query(query, (key,), fetch=True)
        return result[0][0] if result else default_value
    except Exception as e:
        logger.error(f"Failed to get setting {key}: {e}")
        return default_value

def set_setting(key: str, value: str, description: str = None) -> bool:
    """Set bot setting value."""
    try:
        query = '''
            INSERT OR REPLACE INTO bot_settings 
            (setting_key, setting_value, description, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        '''
        params = (key, value, description)
        rows_affected = db_manager.execute_query(query, params)
        return rows_affected > 0
    except Exception as e:
        logger.error(f"Failed to set setting {key}: {e}")
        return False

# ---------------------------------------------------------------------------
# Analytics and Logging
# ---------------------------------------------------------------------------

def log_analytics_event(user_id: int, event_type: str, event_data: Dict = None) -> bool:
    """Log analytics event."""
    if not app_config.enable_analytics:
        return True
        
    try:
        query = '''
            INSERT INTO analytics_events (user_id, event_type, event_data)
            VALUES (?, ?, ?)
        '''
        event_data_json = json.dumps(event_data) if event_data else None
        params = (user_id, event_type, event_data_json)
        rows_affected = db_manager.execute_query(query, params)
        return rows_affected > 0
    except Exception as e:
        logger.error(f"Failed to log analytics event: {e}")
        return False

def log_audit_event(user_id: int, admin_id: int, action: str, details: str = None) -> bool:
    """Log audit event."""
    try:
        query = '''
            INSERT INTO audit_log (user_id, admin_id, action, details)
            VALUES (?, ?, ?, ?)
        '''
        params = (user_id, admin_id, action, details)
        rows_affected = db_manager.execute_query(query, params)
        return rows_affected > 0
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")
        return False

# ---------------------------------------------------------------------------
# Database Maintenance
# ---------------------------------------------------------------------------

def cleanup_old_data(days_to_keep: int = 90) -> Dict[str, int]:
    """Clean up old analytics and audit data."""
    try:
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Clean analytics events
        analytics_query = "DELETE FROM analytics_events WHERE created_at < ?"
        analytics_deleted = db_manager.execute_query(analytics_query, (cutoff_date,))
        
        # Clean audit logs (keep important ones longer)
        audit_query = '''
            DELETE FROM audit_log 
            WHERE created_at < ? AND action NOT IN ('user_banned', 'admin_action')
        '''
        audit_deleted = db_manager.execute_query(audit_query, (cutoff_date,))
        
        # Vacuum database
        db_manager.execute_query("VACUUM")
        
        result = {
            'analytics_deleted': analytics_deleted,
            'audit_deleted': audit_deleted
        }
        
        logger.info(f"Database cleanup completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")
        return {'error': str(e)}

def backup_database(backup_path: str = None) -> bool:
    """Create database backup."""
    try:
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backups/database_backup_{timestamp}.db"
        
        # Ensure backup directory exists
        Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup using SQLite backup API
        with db_manager.get_connection() as source_conn:
            backup_conn = sqlite3.connect(backup_path)
            source_conn.backup(backup_conn)
            backup_conn.close()
        
        logger.info(f"Database backup created: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        return False

# ---------------------------------------------------------------------------
# Backward Compatibility Functions
# ---------------------------------------------------------------------------

def get_db():
    """Get database connection (backward compatibility)."""
    return db_manager.get_connection()

# Export commonly used functions
__all__ = [
    'create_tables', 'test_database_connection',
    'create_user', 'get_user', 'update_user_activity', 'get_all_users',
    'create_subscription', 'get_active_subscription', 'get_expiring_subscriptions', 'expire_subscriptions',
    'get_setting', 'set_setting',
    'log_analytics_event', 'log_audit_event',
    'cleanup_old_data', 'backup_database',
    'get_db', 'db_manager'
]