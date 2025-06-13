#!/usr/bin/env python3
"""
PNP Television Subscription Bot - Hybrid Version
Combines the robust error handling and deployment features of the simple bot
with the advanced functionality of the complete bot system.
"""

import logging
import threading
import sys
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, Filters
from telegram.error import TelegramError

# Import app modules with error handling
try:
    from app.config import TELEGRAM_TOKEN, setup_logging, ADMIN_USER_ID
    from app.database import create_tables, test_database_connection
    from app.scheduler import start_subscription_scheduler
    from app.bot.handlers import (
        start, handle_language_selection, handle_age_verification,
        handle_terms_acceptance, handle_home_menu_buttons, grant_access
    )
    from app.bot.admin_handlers import get_admin_conversation_handler
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required modules are available in the app/ directory")
    sys.exit(1)

# Enhanced configuration
@dataclass
class BotConfig:
    """Enhanced bot configuration with validation."""
    telegram_token: str
    admin_user_id: Optional[int]
    log_level: str = "INFO"
    max_retries: int = 3
    retry_delay: int = 5
    
    @classmethod
    def from_env(cls) -> 'BotConfig':
        """Load configuration from environment with validation."""
        return cls(
            telegram_token=TELEGRAM_TOKEN,
            admin_user_id=int(ADMIN_USER_ID) if ADMIN_USER_ID else None,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            retry_delay=int(os.getenv("RETRY_DELAY", "5"))
        )
    
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.telegram_token:
            logger.error("❌ TELEGRAM_TOKEN is not configured")
            return False
        if len(self.telegram_token) < 40:
            logger.error("❌ TELEGRAM_TOKEN appears to be invalid (too short)")
            return False
        return True

# Initialize configuration
config = BotConfig.from_env()

# Enhanced logging setup
def setup_enhanced_logging() -> None:
    """Setup enhanced logging with rotation and multiple handlers."""
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # File handler for detailed logs
    try:
        file_handler = logging.FileHandler('logs/bot.log', encoding='utf-8')
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"⚠️  Could not setup file logging: {e}")
    
    # Error file handler
    try:
        error_handler = logging.FileHandler('logs/errors.log', encoding='utf-8')
        error_handler.setFormatter(detailed_formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
    except Exception as e:
        print(f"⚠️  Could not setup error logging: {e}")

logger = logging.getLogger(__name__)

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    dirs = ['logs', 'data', 'backups']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        logger.debug(f"Directory '{dir_name}' ready")

def validate_environment() -> bool:
    """Validate the complete environment setup."""
    logger.info("🔧 Validating environment...")
    
    # Check configuration
    if not config.validate():
        return False
    
    # Test database connection
    try:
        if not test_database_connection():
            logger.error("❌ Database connection test failed")
            return False
        logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database validation error: {e}")
        return False
    
    # Check admin configuration
    if config.admin_user_id:
        logger.info(f"✅ Admin user configured: {config.admin_user_id}")
    else:
        logger.warning("⚠️  No admin user configured")
    
    logger.info("✅ Environment validation completed")
    return True

def register_handlers_safely(dispatcher) -> bool:
    """Register bot handlers with comprehensive error handling."""
    try:
        logger.info("📋 Registering bot handlers...")
        
        # 1. Add the admin conversation handler (must be first for entry_points)
        admin_handler = get_admin_conversation_handler()
        if admin_handler:
            dispatcher.add_handler(admin_handler)
            logger.info("✅ Admin conversation handler registered")
        else:
            logger.warning("⚠️  Admin handler not available")

        # 2. Add user-facing handlers
        dispatcher.add_handler(CommandHandler('start', start))
        logger.info("✅ Start command handler registered")
        
        # 3. Secure the /grant command to only be used by the admin
        if config.admin_user_id:
            dispatcher.add_handler(
                CommandHandler(
                    'grant', 
                    grant_access, 
                    filters=Filters.user(user_id=config.admin_user_id)
                )
            )
            logger.info("✅ Grant command handler registered (admin only)")

        # 4. Onboarding Callbacks
        callback_handlers = [
            (handle_language_selection, '^set_lang_'),
            (handle_age_verification, '^age_verify_'),
            (handle_terms_acceptance, '^terms_accept$'),
            (handle_home_menu_buttons, '^home_'),
        ]
        
        for handler_func, pattern in callback_handlers:
            try:
                dispatcher.add_handler(CallbackQueryHandler(handler_func, pattern=pattern))
                logger.debug(f"✅ Callback handler registered: {pattern}")
            except Exception as e:
                logger.error(f"❌ Failed to register callback handler {pattern}: {e}")
                return False
        
        logger.info("✅ All bot handlers registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Critical error registering handlers: {e}", exc_info=True)
        return False

def start_scheduler_safely() -> Optional[threading.Thread]:
    """Start the subscription scheduler with error handling."""
    try:
        logger.info("🕐 Starting subscription management scheduler...")
        scheduler_thread = threading.Thread(
            target=start_subscription_scheduler, 
            daemon=True,
            name="SubscriptionScheduler"
        )
        scheduler_thread.start()
        logger.info("✅ Scheduler started successfully")
        return scheduler_thread
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}", exc_info=True)
        return None

def run_bot_with_retry() -> bool:
    """Run bot with retry mechanism and comprehensive error handling."""
    for attempt in range(config.max_retries):
        try:
            logger.info(f"🤖 Starting bot (attempt {attempt + 1}/{config.max_retries})...")
            
            # Create updater
            updater = Updater(token=config.telegram_token, use_context=True)
            dispatcher = updater.dispatcher
            
            # Register handlers
            if not register_handlers_safely(dispatcher):
                raise Exception("Handler registration failed")
            
            # Start polling
            updater.start_polling(
                poll_interval=1.0,
                timeout=10,
                read_latency=2.0,
                drop_pending_updates=True
            )
            
            logger.info("🚀 Bot started successfully and is polling for updates")
            
            # Keep the bot running
            updater.idle()
            return True
            
        except TelegramError as e:
            logger.error(f"❌ Telegram API error (attempt {attempt + 1}): {e}")
            if attempt < config.max_retries - 1:
                logger.info(f"⏳ Retrying in {config.retry_delay} seconds...")
                import time
                time.sleep(config.retry_delay)
            continue
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user (Ctrl+C)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Unexpected error (attempt {attempt + 1}): {e}", exc_info=True)
            if attempt < config.max_retries - 1:
                logger.info(f"⏳ Retrying in {config.retry_delay} seconds...")
                import time
                time.sleep(config.retry_delay)
            continue
    
    logger.critical("❌ All retry attempts failed. Bot cannot start.")
    return False

def run_bot():
    """Main bot runner with enhanced error handling."""
    try:
        success = run_bot_with_retry()
        if not success:
            sys.exit(1)
    except Exception as e:
        logger.critical(f"❌ Critical error in bot runner: {e}", exc_info=True)
        sys.exit(1)

def main():
    """Enhanced main function with comprehensive startup sequence."""
    print("🤖 PNP Television Subscription Bot - Hybrid Version")
    print("=" * 60)
    
    try:
        # Setup enhanced logging first
        setup_enhanced_logging()
        logger.info("🚀 Application starting...")
        
        # Ensure required directories
        ensure_directories()
        
        # Validate environment
        if not validate_environment():
            logger.critical("❌ Environment validation failed")
            sys.exit(1)
        
        # Initialize database
        logger.info("🗄️  Initializing database...")
        try:
            create_tables()
            logger.info("✅ Database initialized successfully")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            sys.exit(1)
        
        # Start scheduler
        scheduler_thread = start_scheduler_safely()
        if not scheduler_thread:
            logger.warning("⚠️  Scheduler failed to start - continuing without it")
        
        # Run the bot
        logger.info("🤖 Starting Telegram bot...")
        run_bot()
        
    except KeyboardInterrupt:
        logger.info("🛑 Application stopped by user")
    except Exception as e:
        logger.critical(f"❌ Critical application error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("🏁 Application shutting down")

if __name__ == "__main__":
    main()