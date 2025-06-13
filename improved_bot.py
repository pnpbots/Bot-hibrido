#!/usr/bin/env python3
"""
Simplified Subscription Bot for PNP Television.
Based on provided standalone script, integrated into repository structure.
Enhanced with improved error handling, validation, and robustness.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
from dataclasses import dataclass

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes
)
from telegram.error import TelegramError

# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------

@dataclass
class BotConfig:
    """Bot configuration from environment variables."""
    bot_token: str
    admin_ids: List[int]
    channel_id: str
    channel_name: str
    
    @classmethod
    def from_env(cls) -> 'BotConfig':
        """Load configuration from environment variables."""
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        admin_ids = []
        if admin_ids_str:
            admin_ids = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip().isdigit()]
        
        return cls(
            bot_token=os.getenv("BOT_TOKEN", ""),
            admin_ids=admin_ids,
            channel_id=os.getenv("CHANNEL_ID", "@your_private_channel"),
            channel_name=os.getenv("CHANNEL_NAME", "PNP Television")
        )
    
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.bot_token:
            logger.error("❌ BOT_TOKEN no configurado")
            return False
        return True

# Initialize configuration
config = BotConfig.from_env()

# Plan definitions - UNCHANGED
PLANS = {
    "week": {
        "name": "WEEK PASS",
        "price": "$14.99",
        "days": 7,
        "description": "Acceso total a PNP TV por 7 días 🔥"
    },
    "month": {
        "name": "MONTH PASS",
        "price": "$24.99",
        "days": 30,
        "description": "Un mes entero de placer visual sin límites 💦"
    },
    "3month": {
        "name": "3 MONTH PASS",
        "price": "$49.99",
        "days": 90,
        "description": "3 meses de acceso VIP. ¡Ahorra y disfruta más! 💎"
    },
    "halfyear": {
        "name": "1/2 YEAR PASS",
        "price": "$79.99",
        "days": 180,
        "description": "6 meses de acceso full a la experiencia PNP 🔥🔥"
    },
    "year": {
        "name": "1 YEAR PASS",
        "price": "$99.99",
        "days": 365,
        "description": "Todo un año con los shows más calientes de PNP 🖤"
    },
    "lifetime": {
        "name": "LIFETIME PASS",
        "price": "$149.99",
        "days": 9999,
        "description": "Acceso ilimitado para siempre 🖤🔥"
    }
}

# Payment links from environment
PAYMENT_LINKS = {
    "week": os.getenv("WEEK_PAYMENT_LINK", ""),
    "month": os.getenv("MONTH_PAYMENT_LINK", ""),
    "3month": os.getenv("3MONTH_PAYMENT_LINK", ""),
    "halfyear": os.getenv("HALFYEAR_PAYMENT_LINK", ""),
    "year": os.getenv("YEAR_PAYMENT_LINK", ""),
    "lifetime": os.getenv("LIFETIME_PAYMENT_LINK", "")
}

# Message templates - UNCHANGED
MESSAGES = {
    "welcome": f"""
🎬 Bienvenidx a **{config.channel_name}**

Tu portal exclusivo a la experiencia más intensa y provocadora de la red.

🌈 **¿Qué incluye tu suscripción?**
• Acceso a shows en vivo y grabados
• Performers calientes y sin censura
• Llamadas privadas y salas VIP
• Comunidad 24/7 en constante expansión

👉 Elige un plan para entrar al universo de PNP.
""",
    "subscription_status_active": "✅ Tu acceso a **PNP Television** está ACTIVO hasta el: {expiry_date}",
    "subscription_status_inactive": "🚫 No tienes una suscripción activa.\nActiva tu acceso para entrar a los canales privados 🔐",
    "plans_header": "💳 **Elige tu Pase PNP:**",
    "access_granted": """
🎉 Acceso confirmado

Tu pase **{plan_name}** ya está activo.

🔗 Aquí tienes tu enlace exclusivo. Úsalo solo tú:
👇👇👇
""",
    "help_text": """
🛠 **Centro de Soporte PNP**

Comandos disponibles:
• `/start` → Menú principal
• `/status` → Ver tu suscripción
• `/plans` → Ver opciones de pase

👑 Soporte directo: @soporte_pnptv
"""
}

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

def setup_logging() -> None:
    """Setup logging configuration."""
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data persistence helpers
# ---------------------------------------------------------------------------

def ensure_data_directory() -> None:
    """Ensure data directory exists."""
    Path('data').mkdir(exist_ok=True)

def load_users() -> Dict:
    """Load users data from JSON file with improved error handling."""
    ensure_data_directory()
    users_file = Path('data/users.json')
    
    try:
        if not users_file.exists():
            logger.info("Users file not found, creating new one")
            return {}
            
        with open(users_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.debug(f"Loaded {len(data)} users from file")
            return data
            
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in users file: {e}")
        # Backup corrupted file
        backup_file = users_file.with_suffix(f'.json.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        try:
            users_file.rename(backup_file)
            logger.info(f"Corrupted file backed up to {backup_file}")
        except Exception as backup_error:
            logger.error(f"Failed to backup corrupted file: {backup_error}")
        return {}
        
    except Exception as e:
        logger.error(f"Unexpected error loading users: {e}")
        return {}

def save_users(users: Dict) -> bool:
    """Save users data to JSON file with improved error handling."""
    ensure_data_directory()
    users_file = Path('data/users.json')
    temp_file = users_file.with_suffix('.tmp')
    
    try:
        # Write to temporary file first
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False, default=str)
        
        # Atomic move
        temp_file.replace(users_file)
        logger.debug(f"Saved {len(users)} users to file")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save users data: {e}")
        # Clean up temp file
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass
        return False

def validate_user_data(data: Dict) -> Dict:
    """Validate and sanitize user data."""
    safe_data = {}
    
    # Only allow specific fields
    allowed_fields = {
        'id', 'username', 'first_name', 'last_name', 'language_code',
        'created_at', 'last_updated', 'subscription_active', 
        'subscription_until', 'plan', 'payments'
    }
    
    for key, value in data.items():
        if key in allowed_fields:
            safe_data[key] = value
    
    return safe_data

def update_user(user_id: int, data: Dict) -> bool:
    """Update user data with validation."""
    if not isinstance(user_id, int) or user_id <= 0:
        logger.error(f"Invalid user_id: {user_id}")
        return False
    
    try:
        users = load_users()
        user_key = str(user_id)
        
        if user_key not in users:
            users[user_key] = {
                "id": user_id,
                "created_at": datetime.now().isoformat(),
                "subscription_active": False,
                "subscription_until": None,
                "plan": None,
                "payments": 0
            }
            logger.info(f"Created new user record for {user_id}")
        
        # Validate and sanitize incoming data
        safe_data = validate_user_data(data)
        users[user_key].update(safe_data)
        users[user_key]["last_updated"] = datetime.now().isoformat()
        
        return save_users(users)
        
    except Exception as e:
        logger.error(f"Failed to update user {user_id}: {e}")
        return False

def get_user_data(user_id: int) -> Optional[Dict]:
    """Get user data safely."""
    try:
        users = load_users()
        return users.get(str(user_id))
    except Exception as e:
        logger.error(f"Failed to get user data for {user_id}: {e}")
        return None

def is_user_active(user_data: Dict) -> bool:
    """Check if user subscription is active."""
    if not user_data:
        return False
    
    try:
        if not user_data.get('subscription_active', False):
            return False
            
        expiry_str = user_data.get('subscription_until')
        if not expiry_str:
            return False
            
        expiry = datetime.fromisoformat(expiry_str)
        return datetime.now() < expiry
        
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid subscription date format: {e}")
        return False
    except Exception as e:
        logger.error(f"Error checking user active status: {e}")
        return False

# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    try:
        user = update.effective_user
        if not user:
            logger.warning("Received start command without user info")
            return
        
        # Update user data
        user_data = {
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language_code": user.language_code
        }
        
        if not update_user(user.id, user_data):
            logger.error(f"Failed to update user data for {user.id}")
        
        # Get current user info
        info = get_user_data(user.id) or {}
        active = is_user_active(info)
        
        # Prepare status message
        if active and info.get("subscription_until"):
            try:
                expiry_date = datetime.fromisoformat(info["subscription_until"]).strftime('%d/%m/%Y')
                status_msg = MESSAGES["subscription_status_active"].format(expiry_date=expiry_date)
            except Exception:
                status_msg = MESSAGES["subscription_status_inactive"]
        else:
            status_msg = MESSAGES["subscription_status_inactive"]
        
        # Build keyboard
        keyboard = [
            [InlineKeyboardButton("💎 Ver Planes", callback_data="show_plans")],
            [InlineKeyboardButton("👤 Mi Estado", callback_data="my_status")],
            [InlineKeyboardButton("❓ Ayuda", callback_data="help")]
        ]
        
        if user.id in config.admin_ids:
            keyboard.append([InlineKeyboardButton("👑 Admin", callback_data="admin_panel")])
        
        # Handle both callback and message
        message_text = f"{MESSAGES['welcome']}\n\n{status_msg}"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        logger.info(f"Start command handled for user {user.id}")
        
    except TelegramError as e:
        logger.error(f"Telegram error in start_command: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in start_command: {e}")

async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available subscription plans."""
    try:
        query = update.callback_query
        if query:
            await query.answer()
        
        message = MESSAGES["plans_header"]
        keyboard = []
        
        for plan_id, plan_info in PLANS.items():
            message += f"\n\n💳 *{plan_info['name']}* - {plan_info['price']}\n📝 {plan_info['description']}"
            keyboard.append([
                InlineKeyboardButton(
                    f"{plan_info['name']} - {plan_info['price']}",
                    callback_data=f"select_plan_{plan_id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="back_to_start")])
        
        if query:
            await query.edit_message_text(
                message, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                message, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode='Markdown'
            )
            
        logger.info("Plans displayed successfully")
        
    except TelegramError as e:
        logger.error(f"Telegram error in show_plans: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in show_plans: {e}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current subscription status."""
    try:
        user = update.effective_user
        if not user:
            return
        
        info = get_user_data(user.id) or {}
        active = is_user_active(info)
        
        if active and info.get("subscription_until"):
            try:
                expiry = datetime.fromisoformat(info["subscription_until"]).strftime('%d/%m/%Y')
                text = MESSAGES["subscription_status_active"].format(expiry_date=expiry)
            except Exception:
                text = MESSAGES["subscription_status_inactive"]
        else:
            text = MESSAGES["subscription_status_inactive"]
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, parse_mode='Markdown')
            
        logger.info(f"Status displayed for user {user.id}")
        
    except TelegramError as e:
        logger.error(f"Telegram error in status_command: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in status_command: {e}")

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle plan selection."""
    try:
        query = update.callback_query
        if not query:
            return
            
        await query.answer()
        
        # Extract plan ID
        plan_id = query.data.split("_")[-1]
        plan_info = PLANS.get(plan_id)
        
        if not plan_info:
            await query.edit_message_text("❌ Plan no válido")
            logger.warning(f"Invalid plan selected: {plan_id}")
            return
        
        payment_link = PAYMENT_LINKS.get(plan_id, "")
        if not payment_link:
            await query.edit_message_text("❌ Enlace de pago no disponible")
            logger.error(f"No payment link for plan: {plan_id}")
            return
        
        instructions = f"""
💳 **Instrucciones de Pago**

📝 Plan: {plan_info['name']}
💰 Precio: {plan_info['price']}

1️⃣ Haz clic en el botón de pago
2️⃣ Finaliza tu compra en Bold.co
3️⃣ Envíanos el comprobante a @soporte_pnptv
4️⃣ Recibe tu acceso exclusivo al canal
"""
        
        keyboard = [
            [InlineKeyboardButton("💳 Pagar Ahora", url=payment_link)],
            [InlineKeyboardButton("🔙 Ver Otros Planes", callback_data="show_plans")]
        ]
        
        await query.edit_message_text(
            instructions, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='Markdown'
        )
        
        logger.info(f"Plan {plan_id} selected by user {query.from_user.id}")
        
    except TelegramError as e:
        logger.error(f"Telegram error in select_plan: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in select_plan: {e}")

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help information."""
    try:
        query = update.callback_query
        
        if query:
            await query.answer()
            await query.edit_message_text(
                MESSAGES["help_text"], 
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💎 Ver Planes", callback_data="show_plans")],
                    [InlineKeyboardButton("🔙 Volver", callback_data="back_to_start")]
                ]), 
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(MESSAGES["help_text"], parse_mode='Markdown')
            
        logger.info("Help displayed")
        
    except TelegramError as e:
        logger.error(f"Telegram error in show_help: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in show_help: {e}")

# ---------------------------------------------------------------------------
# Callback dispatcher
# ---------------------------------------------------------------------------

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries with improved error handling."""
    query = update.callback_query
    if not query:
        return
    
    try:
        data = query.data
        logger.debug(f"Handling callback: {data} from user {query.from_user.id}")
        
        if data == "show_plans":
            await show_plans(update, context)
        elif data.startswith("select_plan_"):
            await select_plan(update, context)
        elif data == "help":
            await show_help(update, context)
        elif data == "my_status":
            await status_command(update, context)
        elif data == "back_to_start":
            await start_command(update, context)
        elif data == "admin_panel":
            # Admin functionality placeholder
            await query.answer("🚧 Panel de admin en desarrollo")
        else:
            await query.answer("❌ Acción no reconocida")
            logger.warning(f"Unknown callback data: {data}")
            
    except TelegramError as e:
        logger.error(f"Telegram error in handle_callbacks: {e}")
        try:
            await query.answer("❌ Error procesando solicitud")
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Unexpected error in handle_callbacks: {e}")
        try:
            await query.answer("❌ Error interno")
        except Exception:
            pass

# ---------------------------------------------------------------------------
# Bot entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Main bot entry point with improved error handling."""
    # Setup logging
    setup_logging()
    
    # Validate configuration
    if not config.validate():
        return
    
    try:
        # Create application
        app = ApplicationBuilder().token(config.bot_token).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("plans", show_plans))
        app.add_handler(CommandHandler("help", show_help))
        app.add_handler(CommandHandler("status", status_command))
        app.add_handler(CallbackQueryHandler(handle_callbacks))
        
        logger.info("🤖 Simple subscription bot iniciado")
        logger.info(f"📋 Admin IDs: {config.admin_ids}")
        logger.info(f"📺 Channel: {config.channel_name}")
        
        # Start polling
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()