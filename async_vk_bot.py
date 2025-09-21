"""
Современная async версия VK Бота с улучшенной архитектурой
"""
import os
import asyncio
import logging
import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

import aiohttp
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from dotenv import load_dotenv

from database import db
from ai_system import ai_system
from console_admin import console_admin

# Загружаем переменные окружения из файла
load_dotenv('ТОКЕНЫ.env')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BotState(Enum):
    """Состояния бота"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    DEMO = "demo"
    ERROR = "error"
    STOPPING = "stopping"

@dataclass
class MessageContext:
    """Контекст сообщения"""
    peer_id: int
    user_id: int
    text: str
    timestamp: datetime
    is_chat: bool
    user_info: Optional[Dict] = None

@dataclass
class BotConfig:
    """Конфигурация бота"""
    vk_token: str
    group_id: int
    groq_api_key: str
    flood_limit: int = 3
    max_message_length: int = 4096
    demo_mode: bool = False
    auto_backup_interval: int = 300  # 5 минут

class AsyncVKBot:
    """Современный асинхронный VK бот с улучшенной архитектурой"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.state = BotState.INITIALIZING
        
        # VK API компоненты
        self.vk_session: Optional[vk_api.VkApi] = None
        self.vk: Optional[object] = None
        self.longpoll: Optional[VkLongPoll] = None
        
        # HTTP клиент для внешних API
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # Статистика и мониторинг
        self.stats = {
            'start_time': datetime.now(),
            'messages_processed': 0,
            'commands_executed': 0,
            'errors_count': 0,
            'last_activity': datetime.now()
        }
        
        # Флуд-контроль
        self.user_last_message: Dict[int, float] = {}
        
        # Инициализируем консольную панель
        console_admin.bot = self
        
        logger.info("🚀 AsyncVKBot инициализирован")
    
    async def initialize(self) -> bool:
        """Асинхронная инициализация бота"""
        try:
            logger.info("🔧 Начинаем инициализацию...")
            
            # Проверяем токены
            if not await self._validate_tokens():
                self.state = BotState.DEMO
                logger.warning("⚠️  Переход в демо-режим")
                return True
            
            # Инициализируем VK API
            await self._init_vk_api()
            
            # Инициализируем HTTP клиент
            await self._init_http_client()
            
            # Инициализируем базу данных
            await self._init_database()
            
            self.state = BotState.RUNNING
            logger.info("✅ Инициализация завершена успешно")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            self.state = BotState.ERROR
            return False
    
    async def _validate_tokens(self) -> bool:
        """Валидация токенов"""
        if not self.config.vk_token or not self.config.group_id:
            logger.warning("⚠️  Токены не установлены")
            return False
        
        if not self.config.vk_token.startswith('vk1.a.'):
            logger.warning("⚠️  Неверный формат VK токена")
            return False
        
        try:
            # Тестируем токен
            test_session = vk_api.VkApi(token=self.config.vk_token)
            test_vk = test_session.get_api()
            test_vk.users.get()
            logger.info("✅ VK токен валиден")
            return True
        except Exception as e:
            logger.warning(f"⚠️  VK токен недействителен: {e}")
            return False
    
    async def _init_vk_api(self):
        """Инициализация VK API"""
        self.vk_session = vk_api.VkApi(token=self.config.vk_token)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkLongPoll(self.vk_session)
        
        # Проверяем права
        await self._check_vk_permissions()
        logger.info("✅ VK API инициализирован")
    
    async def _init_http_client(self):
        """Инициализация HTTP клиента"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.http_session = aiohttp.ClientSession(timeout=timeout)
        logger.info("✅ HTTP клиент инициализирован")
    
    async def _init_database(self):
        """Инициализация базы данных"""
        # База данных уже инициализирована в database.py
        logger.info("✅ База данных готова")
    
    async def _check_vk_permissions(self):
        """Проверка прав VK API"""
        try:
            # Проверяем информацию о пользователе
            user_info = self.vk.users.get()
            logger.info(f"👤 Пользователь: {user_info[0]['first_name']} {user_info[0]['last_name']}")
            
            # Проверяем информацию о группе
            group_info = self.vk.groups.getById(group_id=self.config.group_id)
            logger.info(f"🏢 Группа: {group_info[0]['name']}")
            
            # Проверяем права на сообщения
            self.vk.messages.getConversations(count=1)
            logger.info("💬 Права на сообщения подтверждены")
            
        except Exception as e:
            logger.warning(f"⚠️  Ограничения прав: {e}")
    
    async def run(self):
        """Главный цикл работы бота"""
        if self.state == BotState.DEMO:
            await self._run_demo_mode()
            return
        
        if self.state != BotState.RUNNING:
            logger.error("❌ Бот не готов к работе")
            return
        
        logger.info("🚀 Запуск основного цикла...")
        
        try:
            # Запускаем фоновые задачи
            background_tasks = [
                asyncio.create_task(self._background_stats_updater()),
                asyncio.create_task(self._background_cleanup()),
            ]
            
            # Основной цикл обработки сообщений
            await self._message_loop()
            
        except KeyboardInterrupt:
            logger.info("🛑 Получен сигнал остановки")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            await self._cleanup()
    
    async def _run_demo_mode(self):
        """Демо-режим с симуляцией"""
        logger.info("🎭 Запуск демо-режима...")
        
        demo_messages = [
            ("2000000001", "привет"),
            ("2000000001", "помощь"),
            ("2000000001", "тест"),
            ("2000000001", "ии как дела?"),
            ("2000000002", "hello"),
            ("2000000001", "спасибо")
        ]
        
        for peer_id, message in demo_messages:
            await asyncio.sleep(3)
            logger.info(f"📨 Получено сообщение от {peer_id}: {message}")
            
            context = MessageContext(
                peer_id=int(peer_id),
                user_id=1,
                text=message,
                timestamp=datetime.now(),
                is_chat=True
            )
            
            await self._process_message(context)
        
        # Продолжаем демо
        while True:
            await asyncio.sleep(10)
            logger.info("💤 Демо режим работает...")
    
    async def _message_loop(self):
        """Основной цикл обработки сообщений"""
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                await self._handle_new_message(event)
    
    async def _handle_new_message(self, event):
        """Обработка нового сообщения"""
        try:
            # Проверяем что это беседа
            if not self._is_chat_conversation(event.peer_id):
                return
            
            # Создаем контекст сообщения
            context = MessageContext(
                peer_id=event.peer_id,
                user_id=event.user_id,
                text=event.text.strip(),
                timestamp=datetime.now(),
                is_chat=True
            )
            
            # Проверяем флуд-контроль
            if not await self._check_flood_control(context.user_id):
                return
            
            # Обрабатываем сообщение
            await self._process_message(context)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения: {e}")
            self.stats['errors_count'] += 1
    
    async def _process_message(self, context: MessageContext):
        """Обработка сообщения"""
        self.stats['messages_processed'] += 1
        self.stats['last_activity'] = datetime.now()
        
        message_lower = context.text.lower()
        
        # Обработка команд
        if message_lower in ['помощь', 'help']:
            await self._handle_help_command(context)
        elif message_lower in ['тест', 'test']:
            await self._handle_test_command(context)
        elif message_lower.startswith('ии ') and len(context.text) > 3:
            await self._handle_ai_command(context)
        elif any(word in message_lower for word in ['привет', 'hello', 'hi']):
            await self._handle_greeting(context)
        else:
            await self._handle_unknown_message(context)
    
    async def _handle_help_command(self, context: MessageContext):
        """Обработка команды помощи"""
        help_text = """🤖 VK Бот Fusionbot v6.0

📋 Доступные команды:
• помощь / help - эта справка
• тест / test - тестовое сообщение
• ии [вопрос] - поговорить с ИИ
• привет - приветствие

🎯 Особенности:
• Система рангов пользователей
• ИИ ответы с fallback
• Защита от флуда
• Работа только в беседах

💡 Просто напишите сообщение для общения!"""
        
        await self._send_message(context.peer_id, help_text)
        self.stats['commands_executed'] += 1
    
    async def _handle_test_command(self, context: MessageContext):
        """Обработка тестовой команды"""
        test_text = f"""✅ Тест пройден! Бот работает нормально.

📊 Статистика:
• Время: {datetime.now().strftime('%H:%M:%S')}
• Сообщений обработано: {self.stats['messages_processed']}
• Время работы: {datetime.now() - self.stats['start_time']}
• Режим: {'Демо' if self.state == BotState.DEMO else 'Рабочий'}"""
        
        await self._send_message(context.peer_id, test_text)
        self.stats['commands_executed'] += 1
    
    async def _handle_ai_command(self, context: MessageContext):
        """Обработка ИИ команды"""
        question = context.text[3:].strip()
        ai_response = await ai_system.get_ai_response(question)
        await self._send_message(context.peer_id, f"🧠 {ai_response}")
        self.stats['commands_executed'] += 1
    
    async def _handle_greeting(self, context: MessageContext):
        """Обработка приветствия"""
        greeting = f"""👋 Привет! Я VK Бот Fusionbot v6.0

🎯 У меня есть система рангов, ИИ помощник и много интересных функций!

💡 Напиши 'помощь' для списка команд или просто общайся со мной!"""
        
        await self._send_message(context.peer_id, greeting)
    
    async def _handle_unknown_message(self, context: MessageContext):
        """Обработка неизвестного сообщения"""
        # Простое эхо или ИИ ответ
        if len(context.text) > 10:
            ai_response = await ai_system.get_ai_response(context.text)
            await self._send_message(context.peer_id, f"💭 {ai_response}")
    
    async def _send_message(self, peer_id: int, message: str, keyboard: Optional[str] = None):
        """Асинхронная отправка сообщения"""
        if self.state == BotState.DEMO:
            logger.info(f"🎭 ДЕМО: Сообщение в чат {peer_id}: {message[:100]}...")
            return
        
        try:
            params = {
                'peer_id': peer_id,
                'message': message,
                'random_id': get_random_id()
            }
            
            if keyboard:
                params['keyboard'] = keyboard
            
            self.vk.messages.send(**params)
            logger.info(f"📤 Сообщение отправлено в чат {peer_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
            self.stats['errors_count'] += 1
    
    def _is_chat_conversation(self, peer_id: int) -> bool:
        """Проверка что это беседа"""
        return peer_id > 2000000000
    
    async def _check_flood_control(self, user_id: int) -> bool:
        """Проверка флуд-контроля"""
        current_time = time.time()
        
        if user_id in self.user_last_message:
            time_diff = current_time - self.user_last_message[user_id]
            if time_diff < self.config.flood_limit:
                return False
        
        self.user_last_message[user_id] = current_time
        return True
    
    async def _background_stats_updater(self):
        """Фоновая задача обновления статистики"""
        while self.state == BotState.RUNNING:
            await asyncio.sleep(60)  # Обновляем каждую минуту
            console_admin.update_stats('messages_processed', 0)
    
    async def _background_cleanup(self):
        """Фоновая задача очистки"""
        while self.state == BotState.RUNNING:
            await asyncio.sleep(300)  # Очищаем каждые 5 минут
            
            # Очищаем старые записи флуд-контроля
            current_time = time.time()
            old_users = [
                user_id for user_id, last_time in self.user_last_message.items()
                if current_time - last_time > 3600  # 1 час
            ]
            for user_id in old_users:
                del self.user_last_message[user_id]
    
    async def _cleanup(self):
        """Очистка ресурсов"""
        logger.info("🧹 Очистка ресурсов...")
        
        if self.http_session:
            await self.http_session.close()
        
        self.state = BotState.STOPPING
        logger.info("✅ Очистка завершена")

async def main():
    """Главная функция"""
    # Создаем конфигурацию
    config = BotConfig(
        vk_token=os.getenv('VK_TOKEN', ''),
        group_id=int(os.getenv('VK_GROUP_ID', 0)),
        groq_api_key=os.getenv('GROQ_API_KEY', ''),
        demo_mode=not os.getenv('VK_TOKEN') or not os.getenv('VK_GROUP_ID')
    )
    
    # Создаем и запускаем бота
    bot = AsyncVKBot(config)
    
    if await bot.initialize():
        await bot.run()
    else:
        logger.error("❌ Не удалось инициализировать бота")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")
    finally:
        input("\n👆 Нажми Enter для выхода...")

