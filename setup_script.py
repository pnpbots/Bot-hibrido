#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup automático para Bot Modular de Telegram
Crea toda la estructura de archivos y configuraciones necesarias
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

class BotSetup:
    """Configurador automático del bot de Telegram"""
    
    def __init__(self):
        self.project_name = "telegram_bot"
        self.base_path = Path.cwd() / self.project_name
        self.created_files = []
        self.created_dirs = []
    
    def create_structure(self):
        """Crea la estructura completa del proyecto"""
        print("🚀 Iniciando setup del Bot Modular de Telegram...")
        print(f"📁 Creando proyecto en: {self.base_path}")
        
        # Crear estructura de directorios
        self._create_directories()
        
        # Crear archivos de configuración
        self._create_config_files()
        
        # Crear handlers
        self._create_handlers()
        
        # Crear servicios
        self._create_services()
        
        # Crear utilidades
        self._create_utils()
        
        # Crear modelos
        self._create_models()
        
        # Crear archivo principal
        self._create_main_file()
        
        # Crear archivos de proyecto
        self._create_project_files()
        
        # Mostrar resumen
        self._show_summary()
    
    def _create_directories(self):
        """Crea la estructura de directorios"""
        directories = [
            "",  # directorio raíz del proyecto
            "config",
            "handlers", 
            "services",
            "models",
            "utils",
            "logs"
        ]
        
        for dir_name in directories:
            dir_path = self.base_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            
            if dir_name:  # No mostrar el directorio raíz
                self.created_dirs.append(dir_name)
                print(f"✅ Directorio creado: {dir_name}/")
    
    def _create_config_files(self):
        """Crea archivos de configuración"""
        files = {
            "config/__init__.py": "",
            "config/settings.py": self._get_settings_content(),
            "config/logging_config.py": self._get_logging_config_content()
        }
        
        self._write_files(files)
    
    def _create_handlers(self):
        """Crea archivos de handlers"""
        files = {
            "handlers/__init__.py": "",
            "handlers/base_handler.py": self._get_base_handler_content(),
            "handlers/start_handler.py": self._get_start_handler_content(),
            "handlers/menu_handler.py": self._get_menu_handler_content(),
            "handlers/content_handler.py": self._get_content_handler_content(),
            "handlers/subscription_handler.py": self._get_subscription_handler_content(),
            "handlers/support_handler.py": self._get_support_handler_content()
        }
        
        self._write_files(files)
    
    def _create_services(self):
        """Crea archivos de servicios"""
        files = {
            "services/__init__.py": "",
            "services/keyboard_service.py": self._get_keyboard_service_content(),
            "services/message_service.py": self._get_message_service_content(),
            "services/user_service.py": self._get_user_service_content()
        }
        
        self._write_files(files)
    
    def _create_utils(self):
        """Crea archivos de utilidades"""
        files = {
            "utils/__init__.py": "",
            "utils/decorators.py": self._get_decorators_content(),
            "utils/validators.py": self._get_validators_content(),
            "utils/constants.py": self._get_constants_content()
        }
        
        self._write_files(files)
    
    def _create_models(self):
        """Crea archivos de modelos"""
        files = {
            "models/__init__.py": "",
            "models/user.py": self._get_user_model_content(),
            "models/subscription.py": self._get_subscription_model_content()
        }
        
        self._write_files(files)
    
    def _create_main_file(self):
        """Crea el archivo principal del bot"""
        files = {
            "main.py": self._get_main_content()
        }
        
        self._write_files(files)
    
    def _create_project_files(self):
        """Crea archivos del proyecto"""
        files = {
            "requirements.txt": self._get_requirements_content(),
            ".env.template": self._get_env_template_content(),
            ".gitignore": self._get_gitignore_content(),
            "README.md": self._get_readme_content()
        }
        
        self._write_files(files)
    
    def _write_files(self, files: Dict[str, str]):
        """Escribe múltiples archivos"""
        for file_path, content in files.items():
            full_path = self.base_path / file_path
            
            try:
                full_path.write_text(content, encoding='utf-8')
                self.created_files.append(file_path)
                print(f"✅ Archivo creado: {file_path}")
            except Exception as e:
                print(f"❌ Error creando {file_path}: {e}")
    
    def _show_summary(self):
        """Muestra resumen del setup"""
        print("\n" + "="*60)
        print("🎉 SETUP COMPLETADO EXITOSAMENTE!")
        print("="*60)
        
        print(f"\n📊 RESUMEN:")
        print(f"   📁 Directorios creados: {len(self.created_dirs)}")
        print(f"   📄 Archivos creados: {len(self.created_files)}")
        print(f"   📍 Ubicación: {self.base_path}")
        
        print(f"\n📋 PRÓXIMOS PASOS:")
        print(f"   1. cd {self.project_name}")
        print(f"   2. cp .env.template .env")
        print(f"   3. nano .env  # Agregar tu BOT_TOKEN")
        print(f"   4. pip install -r requirements.txt")
        print(f"   5. python main.py")
        
        print(f"\n🔑 IMPORTANTE:")
        print(f"   • Obtén tu BOT_TOKEN de @BotFather en Telegram")
        print(f"   • Configura las variables en el archivo .env")
        print(f"   • Lee el README.md para más información")
        
        print(f"\n🆘 SOPORTE:")
        print(f"   • Documentación completa en README.md")
        print(f"   • Estructura modular para fácil personalización")
        print(f"   • Logs automáticos en la carpeta logs/")
    
    # =========================================================================
    # Contenido de archivos
    # =========================================================================
    
    def _get_main_content(self):
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Modular de Telegram - Archivo Principal
Punto de entrada del bot con arquitectura modular
"""

import asyncio
import logging
from telegram.ext import Application

from config.settings import Settings
from config.logging_config import setup_logging
from handlers.start_handler import StartHandler
from handlers.menu_handler import MenuHandler
from utils.decorators import error_handler

class TelegramBot:
    """Bot principal de Telegram con arquitectura modular"""
    
    def __init__(self):
        # Configurar logging
        setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Validar configuración
        Settings.validate()
        
        # Inicializar aplicación
        self.application = Application.builder().token(Settings.BOT_TOKEN).build()
        
        # Inicializar handlers
        self.start_handler = StartHandler()
        self.menu_handler = MenuHandler()
        
        self.logger.info("✅ Bot inicializado correctamente")
    
    def setup_handlers(self):
        """Configura todos los handlers del bot"""
        try:
            # Registrar handlers de cada módulo
            self.start_handler.register_handlers(self.application)
            self.menu_handler.register_handlers(self.application)
            
            self.logger.info("✅ Handlers registrados correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando handlers: {e}")
            raise
    
    @error_handler
    async def run(self):
        """Ejecuta el bot"""
        try:
            self.setup_handlers()
            
            self.logger.info(f"🚀 Iniciando bot: {Settings.BOT_NAME}")
            self.logger.info(f"🔧 Modo: {Settings.ENVIRONMENT}")
            
            # Iniciar polling
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(
                allowed_updates=['message', 'callback_query']
            )
            
            self.logger.info("🤖 Bot funcionando... (Presiona Ctrl+C para detener)")
            
            # Mantener el bot en ejecución
            await asyncio.Event().wait()
            
        except KeyboardInterrupt:
            self.logger.info("🛑 Bot detenido por el usuario")
        except Exception as e:
            self.logger.error(f"❌ Error crítico: {e}")
            raise
        finally:
            await self.application.stop()
            await self.application.shutdown()

async def main():
    """Función principal asíncrona"""
    bot = TelegramBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n🛑 Bot detenido por el usuario")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
'''
    
    def _get_settings_content(self):
        return '''import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Settings:
    """Configuraciones centralizadas del bot"""
    
    # Información del bot
    BOT_NAME = os.getenv('BOT_NAME', 'ModularBot')
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    BOT_USERNAME = os.getenv('BOT_USERNAME', '@ModularBot')
    
    # Configuración del entorno
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Usuarios administrativos
    ADMIN_USER_IDS = [
        int(uid.strip()) for uid in os.getenv('ADMIN_USER_IDS', '').split(',')
        if uid.strip().isdigit()
    ]
    
    # Configuración de logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = Path('logs')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def validate(cls):
        """Valida que todas las configuraciones requeridas estén presentes"""
        required_settings = ['BOT_TOKEN']
        missing = []
        
        for setting in required_settings:
            if not getattr(cls, setting):
                missing.append(setting)
        
        if missing:
            raise ValueError(f"❌ Configuraciones requeridas faltantes: {missing}")
        
        # Crear directorio de logs
        cls.LOG_DIR.mkdir(exist_ok=True)
        
        return True
'''
    
    def _get_logging_config_content(self):
        return '''import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

from .settings import Settings

def setup_logging():
    """Configura el sistema de logging del bot"""
    
    # Crear directorio de logs
    Settings.LOG_DIR.mkdir(exist_ok=True)
    
    # Configurar formato
    formatter = logging.Formatter(
        Settings.LOG_FORMAT,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, Settings.LOG_LEVEL))
    
    # Handler para archivo con rotación
    file_handler = logging.handlers.RotatingFileHandler(
        Settings.LOG_DIR / f'bot_{datetime.now().strftime("%Y%m%d")}.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, Settings.LOG_LEVEL))
    
    # Agregar handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configurar loggers específicos
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info(f"📋 Logging configurado - Nivel: {Settings.LOG_LEVEL}")
'''
    
    def _get_base_handler_content(self):
        return '''import logging
from abc import ABC, abstractmethod
from telegram.ext import Application

class BaseHandler(ABC):
    """Handler base para todos los módulos"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def register_handlers(self, application: Application):
        """Registra los handlers específicos del módulo"""
        pass
    
    def log_user_action(self, user_id: int, username: str, action: str):
        """Registra acción del usuario"""
        self.logger.info(f"👤 Usuario {user_id} (@{username}): {action}")
'''
    
    def _get_start_handler_content(self):
        return '''from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from .base_handler import BaseHandler
from services.keyboard_service import KeyboardService
from services.message_service import MessageService
from utils.decorators import error_handler

class StartHandler(BaseHandler):
    """Manejador del comando start y bienvenida"""
    
    def __init__(self):
        super().__init__()
        self.keyboard_service = KeyboardService()
        self.message_service = MessageService()
    
    def register_handlers(self, application):
        """Registra handlers del módulo de inicio"""
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
    
    @error_handler
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        user = update.effective_user
        self.log_user_action(user.id, user.username, "comando /start")
        
        # Mensaje de bienvenida
        welcome_text = self.message_service.get_welcome_message(user.first_name)
        
        # Enviar mensaje con menú principal
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=self.keyboard_service.get_main_menu()
        )
        
        # Establecer teclado persistente
        keyboard = self.keyboard_service.get_persistent_keyboard()
        
        await update.message.reply_text(
            "🎯 Accesos rápidos:",
            reply_markup=keyboard
        )
    
    @error_handler  
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        user = update.effective_user
        self.log_user_action(user.id, user.username, "comando /help")
        
        help_text = self.message_service.get_help_message()
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown'
        )
'''
    
    def _get_menu_handler_content(self):
        return '''from telegram import Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes

from .base_handler import BaseHandler
from services.keyboard_service import KeyboardService
from services.message_service import MessageService
from utils.decorators import error_handler

class MenuHandler(BaseHandler):
    """Manejador de navegación de menús"""
    
    def __init__(self):
        super().__init__()
        self.keyboard_service = KeyboardService()
        self.message_service = MessageService()
    
    def register_handlers(self, application):
        """Registra handlers del módulo de menús"""
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_persistent_buttons
        ))
    
    @error_handler
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja todos los callbacks de botones inline"""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        self.log_user_action(user.id, user.username, f"callback: {query.data}")
        
        if query.data == 'back_main':
            await self.show_main_menu(query, context)
        else:
            await query.edit_message_text(
                f"🚧 Función '{query.data}' en desarrollo.\\n\\n"
                "Estamos trabajando para traerte esta funcionalidad pronto."
            )
    
    @error_handler
    async def handle_persistent_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja botones del teclado persistente"""
        text = update.message.text
        user = update.effective_user
        
        self.log_user_action(user.id, user.username, f"botón persistente: {text}")
        
        if text == "🤖 Cristina":
            await update.message.reply_text(
                "🤖 ¡Hola! Soy Cristina, tu asistente virtual.\\n"
                "¿En qué puedo ayudarte hoy?"
            )
        elif text == "💳 Membership":
            await update.message.reply_text(
                f"💳 **Mi Membresía**\\n\\n"
                f"👤 Usuario: {user.first_name}\\n"
                f"🆓 Plan actual: Gratuito\\n"
                f"📅 Miembro desde: Hoy\\n\\n"
                f"💡 Considera actualizar a Premium para más funciones!"
            )
        else:
            await update.message.reply_text(
                "🤔 No entiendo ese comando.\\n"
                "Usa los botones del menú para navegar."
            )
    
    async def show_main_menu(self, query, context):
        """Muestra el menú principal"""
        await query.edit_message_text(
            self.message_service.get_main_menu_message(),
            parse_mode='Markdown',
            reply_markup=self.keyboard_service.get_main_menu()
        )
'''
    
    def _get_keyboard_service_content(self):
        return '''from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

class KeyboardService:
    """Servicio para generar teclados y botones"""
    
    @staticmethod
    def get_main_menu():
        """Menú principal inline"""
        keyboard = [
            [InlineKeyboardButton("📺 Contenido", callback_data='content')],
            [InlineKeyboardButton("🎮 Juegos", callback_data='games')],
            [InlineKeyboardButton("💳 Suscripciones", callback_data='subscriptions')],
            [InlineKeyboardButton("📞 Soporte", callback_data='support')]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_persistent_keyboard(is_premium=False):
        """Teclado persistente"""
        buttons = [
            [KeyboardButton("🤖 Cristina"), KeyboardButton("💳 Membership")]
        ]
        
        if is_premium:
            buttons.append([KeyboardButton("📞 Reservar"), KeyboardButton("🎥 Unirse")])
        
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    @staticmethod
    def get_back_button():
        """Botón de regreso simple"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Volver al menú", callback_data='back_main')]
        ])
'''
    
    def _get_message_service_content(self):
        return '''class MessageService:
    """Servicio para generar mensajes del bot"""
    
    @staticmethod
    def get_welcome_message(user_name: str):
        """Mensaje de bienvenida personalizado"""
        return f"""
🎬 **¡Bienvenido al Bot Modular, {user_name}!**

🚀 Tu plataforma de entretenimiento está lista.

✨ **Lo que puedes hacer:**
• 📺 Acceder al catálogo de contenido
• 🎮 Jugar juegos interactivos
• 💳 Gestionar tu suscripción
• 🤖 Chatear con Cristina (Asistente IA)

👇 Elige una opción para comenzar:
        """.strip()
    
    @staticmethod
    def get_help_message():
        """Mensaje de ayuda"""
        return """
🆘 **Ayuda & Comandos**

**Comandos principales:**
• `/start` - Reiniciar el bot
• `/help` - Mostrar esta ayuda

**Navegación:**
• Usa los botones inline para navegar
• Los botones persistentes están siempre disponibles
• Toca "Volver" para regresar al menú anterior

**Soporte:**
• 🤖 Cristina: Asistencia IA instantánea
• 📞 Soporte: Equipo de soporte humano

¿Necesitas más ayuda? ¡Contacta a nuestro equipo!
        """.strip()
    
    @staticmethod
    def get_main_menu_message():
        """Mensaje del menú principal"""
        return """
🎯 **MENÚ PRINCIPAL**

Bienvenido a tu centro de entretenimiento. Elige una opción:

📺 **Contenido** - Explora nuestra colección
🎮 **Juegos** - Diversión interactiva
💳 **Suscripciones** - Gestiona tu membresía
📞 **Soporte** - Obtén ayuda

**Acceso rápido:**
¡Usa los botones de abajo para acceso instantáneo!
        """.strip()
'''
    
    def _get_decorators_content(self):
        return '''import logging
import functools
from telegram.error import TelegramError

def error_handler(func):
    """Decorador para manejo de errores"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        try:
            return await func(*args, **kwargs)
        except TelegramError as e:
            logger.error(f"❌ Error de Telegram en {func.__name__}: {e}")
        except Exception as e:
            logger.error(f"❌ Error en {func.__name__}: {e}", exc_info=True)
    
    return wrapper
'''
    
    def _get_requirements_content(self):
        return '''python-telegram-bot==20.7
python-dotenv==1.0.0
aiofiles==23.2.1
pydantic==2.5.0
'''
    
    def _get_env_template_content(self):
        return '''# Configuración del Bot de Telegram
BOT_NAME=MiBot
BOT_TOKEN=tu_token_aqui
BOT_USERNAME=@MiBot

# Entorno
ENVIRONMENT=development
DEBUG=true

# Usuarios Admin (IDs separados por comas)
ADMIN_USER_IDS=123456789

# Logging
LOG_LEVEL=INFO
'''
    
    def _get_gitignore_content(self):
        return '''.env
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
logs/
.vscode/
.idea/
'''
    
    def _get_readme_content(self):
        return '''# 🤖 Bot Modular de Telegram

Bot de Telegram con arquitectura modular, escalable y mantenible.

## 🚀 Instalación Rápida

1. **Configurar variables:**
   ```bash
   cp .env.template .env
   nano .env  # Agregar tu BOT_TOKEN
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar bot:**
   ```bash
   python main.py
   ```

## 🔑 Obtener Token

1. Hablar con @BotFather en Telegram
2. Crear nuevo bot con `/newbot`
3. Copiar token al archivo `.env`

## 📁 Estructura

```
telegram_bot/
├── main.py                # Archivo principal
├── config/               # Configuraciones
├── handlers/             # Manejadores de eventos
├── services/             # Lógica de negocio
├── utils/                # Utilidades
└── logs/                 # Archivos de log
```

## 🎯 Funcionalidades

- Menús interactivos
- Teclados persistentes
- Sistema de logging
- Arquitectura modular
- Manejo de errores

## 🆘 Soporte

- Documentación completa en el código
- Estructura fácil de extender
- Logs detallados para debugging

¡Disfruta desarrollando tu bot! 🎉
'''
    
    # Contenidos simplificados para otros archivos
    def _get_content_handler_content(self):
        return '''# Content Handler - Placeholder
from .base_handler import BaseHandler

class ContentHandler(BaseHandler):
    def register_handlers(self, application):
        pass
'''
    
    def _get_subscription_handler_content(self):
        return '''# Subscription Handler - Placeholder
from .base_handler import BaseHandler

class SubscriptionHandler(BaseHandler):
    def register_handlers(self, application):
        pass
'''
    
    def _get_support_handler_content(self):
        return '''# Support Handler - Placeholder
from .base_handler import BaseHandler

class SupportHandler(BaseHandler):
    def register_handlers(self, application):
        pass
'''
    
    def _get_user_service_content(self):
        return '''# User Service - Placeholder
class UserService:
    def __init__(self):
        pass
'''
    
    def _get_validators_content(self):
        return '''# Validators - Placeholder
class Validators:
    @staticmethod
    def validate_username(username: str) -> bool:
        return bool(username)
'''
    
    def _get_constants_content(self):
        return '''# Constants - Placeholder
class BotConstants:
    EMOJI_SUCCESS = "✅"
    EMOJI_ERROR = "❌"
'''
    
    def _get_user_model_content(self):
        return '''# User Model - Placeholder
class User:
    pass
'''
    
    def _get_subscription_model_content(self):
        return '''# Subscription Model - Placeholder
class Subscription:
    pass
'''

def main():
    """Función principal del setup"""
    try:
        setup = BotSetup()
        setup.create_structure()
        
    except KeyboardInterrupt:
        print("\n🛑 Setup cancelado por el usuario")
        
    except Exception as e:
        print(f"\n❌ Error durante el setup: {e}")
        print("Verifica que tengas permisos de escritura en el directorio actual")

if __name__ == "__main__":
    main()
