#!/usr/bin/env python3
"""
Enhanced Bot Handlers for PNP Television Bot
Combines comprehensive functionality with robust error handling.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, User as TelegramUser
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from app.config import app_config, PAYMENT_LINKS
from app.database import (
    create_user, get_user, update_user_activity, get_active_subscription,
    create_subscription, log_analytics_event, log_audit_event, User
)
from app.translations import get_text, set_user_language
from app.services import SettingsService, SubscriptionService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Subscription Plans Configuration
# ---------------------------------------------------------------------------

PLANS = {
    "week": {
        "name": "WEEK PASS",
        "price": "$14.99",
        "days": 7,
        "description_es": "Acceso total a PNP TV por 7 días 🔥",
        "description_en": "Full access to PNP TV for 7 days 🔥"
    },
    "month": {
        "name": "MONTH PASS",
        "price": "$24.99",
        "days": 30,
        "description_es": "Un mes entero de placer visual sin límites 💦",
        "description_en": "A full month of unlimited visual pleasure 💦"
    },
    "3month": {
        "name": "3 MONTH PASS",
        "price": "$49.99",
        "days": 90,
        "description_es": "3 meses de acceso VIP. ¡Ahorra y disfruta más! 💎",
        "description_en": "3 months of VIP access. Save more and enjoy more! 💎"
    },
    "halfyear": {
        "name": "1/2 YEAR PASS",
        "price": "$79.99",
        "days": 180,
        "description_es": "6 meses de acceso full a la experiencia PNP 🔥🔥",
        "description_en": "6 months of full access to the PNP experience 🔥🔥"
    },
    "year": {
        "name": "1 YEAR PASS",
        "price": "$99.99",
        "days": 365,
        "description_es": "Todo un año con los shows más calientes de PNP 🖤",
        "description_en": "A full year with PNP's hottest shows 🖤"
    },
    "lifetime": {
        "name": "LIFETIME PASS",
        "price": "$149.99",
        "days": 9999,
        "description_es": "Acceso ilimitado para siempre 🖤🔥",
        "description_en": "Unlimited access forever 🖤🔥"
    }
}

# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def safe_user_update(telegram_user: TelegramUser) -> Optional[Dict[str, Any]]:
    """Safely update user data and return user info."""
    try:
        # Create user data object
        user_data = User(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            language_code=telegram_user.language_code or 'es'
        )
        
        # Create or update user
        success = create_user(user_data)
        if not success:
            logger.error(f"Failed to create/update user {telegram_user.id}")
            return None
        
        # Update activity
        update_user_activity(telegram_user.id)
        
        # Get updated user info
        return get_user(telegram_user.id)
        
    except Exception as e:
        logger.error(f"Error in safe_user_update for {telegram_user.id}: {e}")
        return None

def get_user_language(user_id: int) -> str:
    """Get user's preferred language."""
    try:
        user_data = get_user(user_id)
        return user_data.get('language_code', 'es') if user_data else 'es'
    except Exception:
        return 'es'

def is_user_subscribed(user_id: int) -> tuple[bool, Optional[Dict]]:
    """Check if user has active subscription."""
    try:
        subscription = get_active_subscription(user_id)
        if subscription:
            end_date = datetime.fromisoformat(subscription['end_date'])
            is_active = datetime.now() < end_date
            return is_active, subscription
        return False, None
    except Exception as e:
        logger.error(f"Error checking subscription for user {user_id}: {e}")
        return False, None

async def safe_edit_message(update: Update, text: str, reply_markup=None, parse_mode='Markdown') -> bool:
    """Safely edit message with error handling."""
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        return True
    except TelegramError as e:
        logger.warning(f"Failed to edit message: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error editing message: {e}")
        return False

async def safe_send_message(update: Update, text: str, reply_markup=None, parse_mode='Markdown') -> bool:
    """Safely send message with error handling."""
    try:
        await update.effective_chat.send_message(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return True
    except TelegramError as e:
        logger.warning(f"Failed to send message: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}")
        return False

# ---------------------------------------------------------------------------
# Main Handlers
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enhanced start command handler."""
    try:
        user = update.effective_user
        if not user:
            logger.warning("Start command received without user info")
            return
        
        # Log analytics event
        log_analytics_event(user.id, 'start_command')
        
        # Update user data safely
        user_data = safe_user_update(user)
        if not user_data:
            await safe_send_message(
                update, 
                "❌ Error interno. Por favor, inténtalo de nuevo más tarde."
            )
            return
        
        # Get user language
        user_lang = get_user_language(user.id)
        
        # Check if user needs onboarding
        if not user_data.get('language_code') or user_data.get('language_code') == 'unknown':
            await show_language_selection(update, context)
            return
        
        # Check subscription status
        is_subscribed, subscription = is_user_subscribed(user.id)
        
        # Prepare welcome message
        welcome_text = get_text('welcome_message', user_lang).format(
            channel_name=app_config.channel_name,
            user_name=user.first_name or user.username or 'Usuario'
        )
        
        # Add subscription status
        if is_subscribed and subscription:
            try:
                end_date = datetime.fromisoformat(subscription['end_date'])
                expiry_str = end_date.strftime('%d/%m/%Y')
                status_text = get_text('subscription_active', user_lang).format(expiry_date=expiry_str)
            except Exception:
                status_text = get_text('subscription_inactive', user_lang)
        else:
            status_text = get_text('subscription_inactive', user_lang)
        
        full_message = f"{welcome_text}\n\n{status_text}"
        
        # Build main menu keyboard
        keyboard = []
        
        if is_subscribed:
            keyboard.append([
                InlineKeyboardButton(
                    get_text('access_channel', user_lang), 
                    url=f"https://t.me/{app_config.channel_id.replace('@', '')}"
                )
            ])
        
        keyboard.extend([
            [InlineKeyboardButton(get_text('view_plans', user_lang), callback_data="home_plans")],
            [InlineKeyboardButton(get_text('my_status', user_lang), callback_data="home_status")],
            [
                InlineKeyboardButton(get_text('settings', user_lang), callback_data="home_settings"),
                InlineKeyboardButton(get_text('help', user_lang), callback_data="home_help")
            ]
        ])
        
        # Add admin button if user is admin
        if user.id == app_config.admin_user_id:
            keyboard.append([
                InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await safe_edit_message(update, full_message, reply_markup)
        else:
            await safe_send_message(update, full_message, reply_markup)
        
        logger.info(f"Start command handled for user {user.id}")
        
    except Exception as e:
        logger.error(f"Error in start handler: {e}", exc_info=True)
        await safe_send_message(
            update, 
            "❌ Error interno. Por favor, contacta al soporte @soporte_pnptv"
        )

async def show_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show language selection menu."""
    try:
        text = """
🌍 **Selecciona tu idioma / Choose your language**

Elige tu idioma preferido para continuar.
Choose your preferred language to continue.
"""
        
        keyboard = [
            [InlineKeyboardButton("🇪🇸 Español", callback_data="set_lang_es")],
            [InlineKeyboardButton("🇺🇸 English", callback_data="set_lang_en")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await safe_edit_message(update, text, reply_markup)
        else:
            await safe_send_message(update, text, reply_markup)
            
    except Exception as e:
        logger.error(f"Error showing language selection: {e}")

async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection."""
    try:
        query = update.callback_query
        if not query:
            return
            
        await query.answer()
        
        user = query.from_user
        language = query.data.split('_')[-1]  # Extract 'es' or 'en'
        
        # Update user language
        user_data = get_user(user.id)
        if user_data:
            # Update language in database
            set_user_language(user.id, language)
            
            # Log analytics
            log_analytics_event(user.id, 'language_selected', {'language': language})
            
            # Continue to age verification
            await show_age_verification(update, context)
        else:
            await safe_edit_message(update, "❌ Error. Por favor, inténtalo de nuevo.")
            
    except Exception as e:
        logger.error(f"Error handling language selection: {e}")

async def show_age_verification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show age verification."""
    try:
        user = update.effective_user
        user_lang = get_user_language(user.id)
        
        text = get_text('age_verification', user_lang)
        
        keyboard = [
            [InlineKeyboardButton(get_text('age_yes', user_lang), callback_data="age_verify_yes")],
            [InlineKeyboardButton(get_text('age_no', user_lang), callback_data="age_verify_no")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(update, text, reply_markup)
        
    except Exception as e:
        logger.error(f"Error showing age verification: {e}")

async def handle_age_verification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle age verification."""
    try:
        query = update.callback_query
        if not query:
            return
            
        await query.answer()
        
        user = query.from_user
        user_lang = get_user_language(user.id)
        verification = query.data.split('_')[-1]  # 'yes' or 'no'
        
        # Log analytics
        log_analytics_event(user.id, 'age_verification', {'verified': verification == 'yes'})
        
        if verification == 'yes':
            await show_terms_acceptance(update, context)
        else:
            # User is underage
            text = get_text('age_restricted', user_lang)
            await safe_edit_message(update, text)
            
    except Exception as e:
        logger.error(f"Error handling age verification: {e}")

async def show_terms_acceptance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show terms and conditions."""
    try:
        user = update.effective_user
        user_lang = get_user_language(user.id)
        
        text = get_text('terms_and_conditions', user_lang)
        
        keyboard = [
            [InlineKeyboardButton(get_text('accept_terms', user_lang), callback_data="terms_accept")],
            [InlineKeyboardButton(get_text('decline_terms', user_lang), callback_data="terms_decline")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(update, text, reply_markup)
        
    except Exception as e:
        logger.error(f"Error showing terms: {e}")

async def handle_terms_acceptance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle terms acceptance."""
    try:
        query = update.callback_query
        if not query:
            return
            
        await query.answer()
        
        user = query.from_user
        user_lang = get_user_language(user.id)
        
        # Log analytics
        log_analytics_event(user.id, 'terms_accepted')
        
        # Mark onboarding as complete
        # You can add a setting or database field for this
        
        # Show success and redirect to main menu
        text = get_text('onboarding_complete', user_lang)
        await safe_edit_message(update, text)
        
        # Wait a moment then show main menu
        import asyncio
        await asyncio.sleep(2)
        await start(update, context)
        
    except Exception as e:
        logger.error(f"Error handling terms acceptance: {e}")

async def handle_home_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle home menu button presses."""
    try:
        query = update.callback_query
        if not query:
            return
            
        await query.answer()
        
        user = query.from_user
        action = query.data.split('_')[1]  # Extract action after 'home_'
        
        # Log analytics
        log_analytics_event(user.id, 'menu_action', {'action': action})
        
        if action == "plans":
            await show_subscription_plans(update, context)
        elif action == "status":
            await show_subscription_status(update, context)
        elif action == "settings":
            await show_user_settings(update, context)
        elif action == "help":
            await show_help_menu(update, context)
        else:
            await query.answer("❌ Acción no reconocida")
            
    except Exception as e:
        logger.error(f"Error handling home menu: {e}")

async def show_subscription_plans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available subscription plans."""
    try:
        user = update.effective_user
        user_lang = get_user_language(user.id)
        
        text = get_text('plans_header', user_lang)
        keyboard = []
        
        for plan_id, plan_info in PLANS.items():
            description_key = f"description_{user_lang}"
            description = plan_info.get(description_key, plan_info['description_es'])
            
            text += f"\n\n💳 *{plan_info['name']}* - {plan_info['price']}\n📝 {description}"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{plan_info['name']} - {plan_info['price']}",
                    callback_data=f"select_plan_{plan_id}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton(get_text('back_to_menu', user_lang), callback_data="back_to_start")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(update, text, reply_markup)
        
    except Exception as e:
        logger.error(f"Error showing plans: {e}")

async def show_subscription_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's subscription status."""
    try:
        user = update.effective_user
        user_lang = get_user_language(user.id)
        
        is_subscribed, subscription = is_user_subscribed(user.id)
        
        if is_subscribed and subscription:
            try:
                end_date = datetime.fromisoformat(subscription['end_date'])
                start_date = datetime.fromisoformat(subscription['start_date'])
                
                text = get_text('detailed_status_active', user_lang).format(
                    plan_type=subscription['plan_type'].upper(),
                    start_date=start_date.strftime('%d/%m/%Y'),
                    end_date=end_date.strftime('%d/%m/%Y'),
                    days_left=(end_date - datetime.now()).days
                )
            except Exception:
                text = get_text('subscription_active_simple', user_lang)
        else:
            text = get_text('subscription_inactive', user_lang)
        
        keyboard = [
            [InlineKeyboardButton(get_text('view_plans', user_lang), callback_data="home_plans")],
            [InlineKeyboardButton(get_text('back_to_menu', user_lang), callback_data="back_to_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(update, text, reply_markup)
        
    except Exception as e:
        logger.error(f"Error showing status: {e}")

async def show_user_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user settings menu."""
    try:
        user = update.effective_user
        user_lang = get_user_language(user.id)
        
        text = get_text('settings_menu', user_lang)
        
        keyboard = [
            [InlineKeyboardButton(get_text('change_language', user_lang), callback_data="settings_language")],
            [InlineKeyboardButton(get_text('notifications', user_lang), callback_data="settings_notifications")],
            [InlineKeyboardButton(get_text('back_to_menu', user_lang), callback_data="back_to_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(update, text, reply_markup)
        
    except Exception as e:
        logger.error(f"Error showing settings: {e}")

async def show_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help menu."""
    try:
        user = update.effective_user
        user_lang = get_user_language(user.id)
        
        text = get_text('help_menu', user_lang)
        
        keyboard = [
            [InlineKeyboardButton(get_text('contact_support', user_lang), url="https://t.me/soporte_pnptv")],
            [InlineKeyboardButton(get_text('back_to_menu', user_lang), callback_data="back_to_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(update, text, reply_markup)
        
    except Exception as e:
        logger.error(f"Error showing help: {e}")

# ---------------------------------------------------------------------------
# Plan Selection and Payment
# ---------------------------------------------------------------------------

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle plan selection."""
    try:
        query = update.callback_query
        if not query:
            return
            
        await query.answer()
        
        user = query.from_user
        user_lang = get_user_language(user.id)
        plan_id = query.data.split("_")[-1]
        
        plan_info = PLANS.get(plan_id)
        if not plan_info:
            await safe_edit_message(update, get_text('invalid_plan', user_lang))
            return
        
        payment_link = PAYMENT_LINKS.get(plan_id, "")
        if not payment_link:
            await safe_edit_message(update, get_text('payment_link_unavailable', user_lang))
            return
        
        # Log analytics
        log_analytics_event(user.id, 'plan_selected', {'plan': plan_id})
        
        text = get_text('payment_instructions', user_lang).format(
            plan_name=plan_info['name'],
            price=plan_info['price']
        )
        
        keyboard = [
            [InlineKeyboardButton(get_text('pay_now', user_lang), url=payment_link)],
            [InlineKeyboardButton(get_text('view_other_plans', user_lang), callback_data="home_plans")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(update, text, reply_markup)
        
    except Exception as e:
        logger.error(f"Error in plan selection: {e}")

# ---------------------------------------------------------------------------
# Admin Functions
# ---------------------------------------------------------------------------

async def grant_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Grant access to a user (admin only)."""
    try:
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Uso: /grant <user_id> <plan_type> [days]\n"
                "Ejemplo: /grant 123456789 month 30"
            )
            return
        
        user_id = int(context.args[0])
        plan_type = context.args[1]
        days = int(context.args[2]) if len(context.args) > 2 else PLANS.get(plan_type, {}).get('days', 30)
        
        # Create subscription
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)
        
        subscription_id = create_subscription(
            user_id=user_id,
            plan_type=plan_type,
            start_date=start_date,
            end_date=end_date,
            payment_amount=0.0  # Admin granted
        )
        
        if subscription_id:
            # Log audit event
            log_audit_event(
                user_id=user_id,
                admin_id=update.effective_user.id,
                action='grant_access',
                details=f'Plan: {plan_type}, Days: {days}'
            )
            
            await update.message.reply_text(
                f"✅ Acceso otorgado exitosamente:\n"
                f"Usuario: {user_id}\n"
                f"Plan: {plan_type}\n"
                f"Duración: {days} días\n"
                f"Vence: {end_date.strftime('%d/%m/%Y')}"
            )
        else:
            await update.message.reply_text("❌ Error otorgando acceso")
            
    except Exception as e:
        logger.error(f"Error granting access: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

# ---------------------------------------------------------------------------
# Callback Query Router
# ---------------------------------------------------------------------------

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route callback queries to appropriate handlers."""
    try:
        query = update.callback_query
        if not query:
            return
        
        data = query.data
        
        # Route to appropriate handler based on callback data
        if data.startswith("set_lang_"):
            await handle_language_selection(update, context)
        elif data.startswith("age_verify_"):
            await handle_age_verification(update, context)
        elif data == "terms_accept":
            await handle_terms_acceptance(update, context)
        elif data.startswith("home_"):
            await handle_home_menu_buttons(update, context)
        elif data.startswith("select_plan_"):
            await select_plan(update, context)
        elif data == "back_to_start":
            await start(update, context)
        else:
            await query.answer("❌ Acción no reconocida")
            
    except Exception as e:
        logger.error(f"Error in callback query handler: {e}")

# Export handlers
__all__ = [
    'start', 'handle_language_selection', 'handle_age_verification',
    'handle_terms_acceptance', 'handle_home_menu_buttons', 'grant_access',
    'handle_callback_query'
]