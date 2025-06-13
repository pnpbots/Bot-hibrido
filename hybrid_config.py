#!/usr/bin/env python3
"""
Enhanced Configuration Module for PNP Television Bot
Combines robust configuration management with validation and fallbacks.
"""

import os
import logging
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

# ---------------------------------------------------------------------------
# Core Configuration Class
# ---------------------------------------------------------------------------

@dataclass
class DatabaseConfig:
    """Database configuration with validation."""
    url: str = "sqlite:///data/pnp_bot.db"
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False
    
    def validate(self) -> bool:
        """Validate database configuration."""
        if self.url.startswith("sqlite://"):
            # Ensure SQLite directory exists
            db_path = Path(self.url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        return True

@dataclass
class PaymentConfig:
    """Payment system configuration."""
    week_link: str = ""
    month_link: str = ""
    three_month_link: str = ""
    half_year_link: str = ""
    year_link: str = ""
    lifetime_link: str = ""
    
    @classmethod
    def from_env(cls) -> 'PaymentConfig':
        """Load payment configuration from environment."""
        return cls(
            week_link=os.getenv("WEEK_PAYMENT_LINK", ""),
            month_link=os.getenv("MONTH_PAYMENT_LINK", ""),
            three_month_link=os.getenv("3MONTH_PAYMENT_LINK", ""),
            half_year_link=os.getenv("HALFYEAR_PAYMENT_LINK", ""),
            year_link=os.getenv("YEAR_PAYMENT_LINK", ""),
            lifetime_link=os.getenv("LIFETIME_PAYMENT_LINK", "")
        )
    
    def get_links_dict(self) -> Dict[str, str]:
        """Get payment links as dictionary for backward compatibility."""
        return {
            "week": self.week_link,
            "month": self.month_link,
            "3month": self.three_month_link,
            "halfyear": self.half_year_link,
            "year": self.year_link,
            "lifetime": self.lifetime_link
        }
    
    def validate(self) -> List[str]:
        """Validate payment configuration and return missing links."""
        links = self.get_links_dict()
        missing = [plan for plan, link in links.items() if not link]
        return missing

@dataclass
class AppConfig:
    """Main application configuration."""
    # Telegram settings
    telegram_token: str = ""
    admin_user_id: Optional[int] = None
    channel_id: str = "@your_private_channel"
    channel_name: str = "PNP Television"
    
    # Database settings
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    # Payment settings
    payments: PaymentConfig = field(default_factory=PaymentConfig)
    
    # Logging settings
    log_level: str = "INFO"
    log_file: str = "logs/bot.log"
    max_log_size: int = 10485760  # 10MB
    backup_count: int = 5
    
    # Bot behavior settings
    max_retries: int = 3
    retry_delay: int = 5
    poll_interval: float = 1.0
    request_timeout: int = 10
    
    # Feature flags
    enable_scheduler: bool = True
    enable_admin_panel: bool = True
    enable_analytics: bool = True
    debug_mode: bool = False
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Load configuration from environment variables."""
        config = cls()
        
        # Load basic settings
        config.telegram_token = os.getenv("BOT_TOKEN", os.getenv("TELEGRAM_TOKEN", ""))
        
        admin_id_str = os.getenv("ADMIN_USER_ID", os.getenv("ADMIN_IDS", ""))
        if admin_id_str:
            try:
                # Handle both single ID and comma-separated IDs (take first one)
                first_id = admin_id_str.split(",")[0].strip()
                config.admin_user_id = int(first_id) if first_id.isdigit() else None
            except (ValueError, IndexError):
                config.admin_user_id = None
        
        config.channel_id = os.getenv("CHANNEL_ID", config.channel_id)
        config.channel_name = os.getenv("CHANNEL_NAME", config.channel_name)
        
        # Load database settings
        config.database.url = os.getenv("DATABASE_URL", config.database.url)
        config.database.echo = os.getenv("DB_ECHO", "false").lower() == "true"
        
        # Load payment settings
        config.payments = PaymentConfig.from_env()
        
        # Load logging settings
        config.log_level = os.getenv("LOG_LEVEL", config.log_level)
        config.log_file = os.getenv("LOG_FILE", config.log_file)
        
        # Load bot behavior settings
        config.max_retries = int(os.getenv("MAX_RETRIES", str(config.max_retries)))
        config.retry_delay = int(os.getenv("RETRY_DELAY", str(config.retry_delay)))
        config.poll_interval = float(os.getenv("POLL_INTERVAL", str(config.poll_interval)))
        config.request_timeout = int(os.getenv("REQUEST_TIMEOUT", str(config.request_timeout)))
        
        # Load feature flags
        config.enable_scheduler = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"
        config.enable_admin_panel = os.getenv("ENABLE_ADMIN_PANEL", "true").lower() == "true"
        config.enable_analytics = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
        config.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        
        return config
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Validate required settings
        if not self.telegram_token:
            issues.append("TELEGRAM_TOKEN/BOT_TOKEN is required")
        elif len(self.telegram_token) < 40:
            issues.append("TELEGRAM_TOKEN appears to be invalid (too short)")
        
        # Validate database
        try:
            if not self.database.validate():
                issues.append("Database configuration is invalid")
        except Exception as e:
            issues.append(f"Database validation error: {e}")
        
        # Validate payment links
        missing_payments = self.payments.validate()
        if missing_payments:
            issues.append(f"Missing payment links: {', '.join(missing_payments)}")
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            issues.append(f"Invalid log level: {self.log_level}")
        
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (for logging/debugging)."""
        config_dict = {
            "telegram_token": "***HIDDEN***" if self.telegram_token else "NOT_SET",
            "admin_user_id": self.admin_user_id,
            "channel_id": self.channel_id,
            "channel_name": self.channel_name,
            "database_url": self.database.url,
            "log_level": self.log_level,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "enable_scheduler": self.enable_scheduler,
            "enable_admin_panel": self.enable_admin_panel,
            "enable_analytics": self.enable_analytics,
            "debug_mode": self.debug_mode,
            "payment_links_configured": len([link for link in self.payments.get_links_dict().values() if link])
        }
        return config_dict

# ---------------------------------------------------------------------------
# Global Configuration Instance
# ---------------------------------------------------------------------------

# Load configuration
app_config = AppConfig.from_env()

# Backward compatibility exports
TELEGRAM_TOKEN = app_config.telegram_token
BOT_TOKEN = app_config.telegram_token  # Alternative name
ADMIN_USER_ID = str(app_config.admin_user_id) if app_config.admin_user_id else ""
CHANNEL_ID = app_config.channel_id
CHANNEL_NAME = app_config.channel_name
DATABASE_URL = app_config.database.url

# Payment links for backward compatibility
PAYMENT_LINKS = app_config.payments.get_links_dict()

# ---------------------------------------------------------------------------
# Logging Setup Function
# ---------------------------------------------------------------------------

def setup_logging() -> None:
    """Enhanced logging setup with rotation and multiple handlers."""
    from logging.handlers import RotatingFileHandler
    
    # Ensure logs directory exists
    Path(app_config.log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, app_config.log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # Rotating file handler
    try:
        file_handler = RotatingFileHandler(
            app_config.log_file,
            maxBytes=app_config.max_log_size,
            backupCount=app_config.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"⚠️  Could not setup file logging: {e}")
    
    # Error file handler
    try:
        error_handler = RotatingFileHandler(
            "logs/errors.log",
            maxBytes=app_config.max_log_size,
            backupCount=app_config.backup_count,
            encoding='utf-8'
        )
        error_handler.setFormatter(detailed_formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
    except Exception as e:
        print(f"⚠️  Could not setup error logging: {e}")

# ---------------------------------------------------------------------------
# Configuration Validation and Reporting
# ---------------------------------------------------------------------------

def validate_config() -> bool:
    """Validate configuration and log results."""
    logger = logging.getLogger(__name__)
    
    issues = app_config.validate()
    
    if issues:
        logger.error("❌ Configuration validation failed:")
        for issue in issues:
            logger.error(f"   - {issue}")
        return False
    
    logger.info("✅ Configuration validation passed")
    
    if app_config.debug_mode:
        logger.debug("📋 Configuration summary:")
        config_dict = app_config.to_dict()
        for key, value in config_dict.items():
            logger.debug(f"   {key}: {value}")
    
    return True

def save_config_backup() -> bool:
    """Save current configuration to backup file."""
    try:
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"config_backup_{timestamp}.json"
        
        config_dict = app_config.to_dict()
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, default=str)
        
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to save config backup: {e}")
        return False

# ---------------------------------------------------------------------------
# Export main configuration for easy access
# ---------------------------------------------------------------------------

__all__ = [
    'app_config',
    'TELEGRAM_TOKEN', 'BOT_TOKEN', 'ADMIN_USER_ID', 
    'CHANNEL_ID', 'CHANNEL_NAME', 'DATABASE_URL', 'PAYMENT_LINKS',
    'setup_logging', 'validate_config', 'save_config_backup'
]