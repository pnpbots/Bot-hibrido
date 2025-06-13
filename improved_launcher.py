#!/usr/bin/env python3
"""
PNP Subscription Bot Launcher
Entry point for the simplified subscription bot with proper error handling,
environment validation, and setup procedures.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import NoReturn

def check_python_version() -> None:
    """Ensure Python version compatibility."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher required")
        print(f"Current version: {sys.version}")
        sys.exit(1)

def setup_directories() -> None:
    """Create required directories."""
    dirs = ["data", "logs"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Directory '{dir_name}' ready")

def validate_environment() -> bool:
    """Validate required environment variables."""
    required_vars = ["BOT_TOKEN"]
    optional_vars = {
        "ADMIN_IDS": "comma-separated list of admin user IDs",
        "CHANNEL_ID": "telegram channel ID (e.g., @your_channel)",
        "CHANNEL_NAME": "display name for the channel",
        "WEEK_PAYMENT_LINK": "payment link for weekly subscription",
        "MONTH_PAYMENT_LINK": "payment link for monthly subscription",
        "3MONTH_PAYMENT_LINK": "payment link for 3-month subscription",
        "HALFYEAR_PAYMENT_LINK": "payment link for 6-month subscription", 
        "YEAR_PAYMENT_LINK": "payment link for yearly subscription",
        "LIFETIME_PAYMENT_LINK": "payment link for lifetime subscription"
    }
    
    # Check required variables
    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    if missing_required:
        print("❌ Missing required environment variables:")
        for var in missing_required:
            print(f"   - {var}")
        print("\nPlease set these variables before running the bot.")
        return False
    
    # Check optional variables and show warnings
    missing_optional = []
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append((var, optional_vars[var]))
    
    if missing_optional:
        print("⚠️  Optional environment variables not set:")
        for var, description in missing_optional:
            print(f"   - {var}: {description}")
        print("\nBot will run with default values for missing optional variables.\n")
    
    # Show configuration summary
    print("📋 Configuration Summary:")
    print(f"   BOT_TOKEN: {'✅ Set' if os.getenv('BOT_TOKEN') else '❌ Missing'}")
    print(f"   ADMIN_IDS: {os.getenv('ADMIN_IDS', 'Not set')}")
    print(f"   CHANNEL_NAME: {os.getenv('CHANNEL_NAME', 'PNP Television (default)')}")
    print(f"   Payment links configured: {sum(1 for link in ['WEEK_PAYMENT_LINK', 'MONTH_PAYMENT_LINK', '3MONTH_PAYMENT_LINK', 'HALFYEAR_PAYMENT_LINK', 'YEAR_PAYMENT_LINK', 'LIFETIME_PAYMENT_LINK'] if os.getenv(link))}/6")
    print()
    
    return True

def setup_logging(level: str = "INFO") -> None:
    """Setup basic logging before bot starts."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PNP Television Subscription Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  BOT_TOKEN              Telegram bot token (required)
  ADMIN_IDS              Comma-separated admin user IDs
  CHANNEL_ID             Target channel ID (e.g., @channel)
  CHANNEL_NAME           Display name for the channel
  *_PAYMENT_LINK         Payment links for each subscription plan

Examples:
  python run_simple_bot.py
  python run_simple_bot.py --log-level DEBUG
  python run_simple_bot.py --validate-only
        """
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate configuration without starting the bot"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="PNP Subscription Bot v1.0"
    )
    
    return parser.parse_args()

def run_bot() -> None:
    """Run the bot with comprehensive error handling."""
    try:
        from bot.simple_subscription_bot import main as bot_main
        print("🚀 Starting PNP Subscription Bot...")
        bot_main()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user (Ctrl+C)")
        sys.exit(0)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required dependencies are installed:")
        print("   pip install python-telegram-bot")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Unexpected error starting bot: {e}")
        logging.exception("Bot startup failed")
        sys.exit(1)

def main() -> None:
    """Main entry point with full setup and validation."""
    args = parse_args()
    
    # Setup logging early
    setup_logging(args.log_level)
    
    print("🤖 PNP Television Subscription Bot")
    print("=" * 40)
    
    # System checks
    print("🔍 Running system checks...")
    check_python_version()
    setup_directories()
    
    # Environment validation
    print("🔧 Validating configuration...")
    if not validate_environment():
        sys.exit(1)
    
    # If only validation requested, exit here
    if args.validate_only:
        print("✅ Configuration validation completed successfully!")
        sys.exit(0)
    
    # Start the bot
    try:
        run_bot()
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()