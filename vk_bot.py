import os
import asyncio
import logging
import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from database import db
from ai_system import ai_system
from console_admin import console_admin

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

class VKBot:
    """Продвинутый VK бот с ИИ и системой рангов"""
    
    def __init__(self):
        # Получаем токены из переменных окружения
        self.vk_token = os.getenv('VK_TOKEN')
        self.group_id = int(os.getenv('VK_GROUP_ID', 0))
        
        # Режим демо если токены не установлены
        self.demo_mode = not self.vk_token or not self.group_id
        
        if self.demo_mode:
            logger.warning("⚠️  ДЕМО РЕЖИМ: VK_TOKEN или VK_GROUP_ID не установлены")
            logger.info("🎭 Бот работает в демонстрационном режиме")
            return
        
        if not self.demo_mode:
            # Инициализация VK API
            self.vk_session = vk_api.VkApi(token=self.vk_token)
            self.vk = self.vk_session.get_api()
            self.longpoll = VkLongPoll(self.vk_session)
        
        # Флуд-контроль
        self.user_last_message = {}
        self.flood_limit = 3  # секунды между сообщениями
        
        # Статистика бота
        self.start_time = datetime.now()
        self.messages_processed = 0
        
        # Инициализируем консольную панель
        console_admin.bot = self
        
        logger.info(f"🤖 VK Бот инициализирован. ID группы: {self.group_id}")
        logger.info(f"🎯 Работаем только в беседах (peer_id > 2000000000)")
        logger.info(f"🧠 ИИ система: Groq → Hugging Face → Локальные ответы")
        logger.info(f"💾 База данных: SQLite с автобекапом каждые 5 минут")
    
    def send_message(self, peer_id: int, message: str, keyboard: Optional[str] = None):
        """Отправка сообщения в ВК"""
        try:
            params = {
                'peer_id': peer_id,
                'message': message,
                'random_id': get_random_id()
            }
            
            if keyboard:
                params['keyboard'] = keyboard
            
            self.vk.messages.send(**params)
            logger.info(f"Сообщение отправлено в чат {peer_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
    
    def is_chat_conversation(self, peer_id: int) -> bool:
        """Проверка что это беседа, а не группа или личка"""
        return peer_id > 2000000000
    
    def extract_user_id(self, text: str) -> Optional[int]:
        """Извлечение ID пользователя из упоминания [id123|@username]"""
        patterns = [
            r'\[id(\d+)\|',  # [id123|@username]
            r'@id(\d+)',     # @id123
            r'id(\d+)'       # id123
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None
    
    def check_flood_control(self, user_id: int) -> bool:
        """Проверка флуд-контроля"""
        current_time = time.time()
        
        if user_id in self.user_last_message:
            time_diff = current_time - self.user_last_message[user_id]
            if time_diff < self.flood_limit:
                return False
        
        self.user_last_message[user_id] = current_time
        return True

    # Основной метод запуска бота
    def run(self):
        """Запуск бота с обработкой ошибок"""
        logger.info("🚀 Запуск VK Бота...")
        
        if self.demo_mode:
            logger.info("🎭 Демонстрационный режим активен")
            logger.info("📝 Для полной работы установите VK_TOKEN и VK_GROUP_ID")
            logger.info("⏸️  Нажмите Ctrl+C для остановки")
            
            # Демо цикл
            try:
                import time
                while True:
                    time.sleep(5)
                    logger.info("💤 Демо режим работает... (установите токены для полной работы)")
            except KeyboardInterrupt:
                logger.info("🛑 Получен сигнал остановки")
            finally:
                logger.info("🛑 Демо режим остановлен")
                input("\n👆 Нажми Enter для выхода...")
            return
        
        try:
            # Проверяем соединение
            self.vk.users.get()
            logger.info("✅ Подключение к VK API успешно")
            
            # Главный цикл обработки сообщений
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    # Работаем только с беседами
                    if not self.is_chat_conversation(event.peer_id):
                        continue
                        
                    # Простая обработка сообщений
                    message = event.text.strip()
                    message_lower = message.lower()
                    
                    # Обработка команд без слешей
                    if message_lower in ['помощь', 'help']:
                        self.send_message(event.peer_id, "🤖 VK Бот работает! Доступные команды:\nпомощь - эта справка\nтест - тестовое сообщение\nии [вопрос] - поговорить с ИИ")
                    elif message_lower in ['тест', 'test']:
                        self.send_message(event.peer_id, f"✅ Тест пройден! Бот работает нормально.\nВремя: {datetime.now().strftime('%H:%M:%S')}")
                    elif message_lower.startswith('ии ') and len(message) > 3:
                        # ИИ ответ
                        question = message[3:].strip()
                        ai_response = asyncio.run(ai_system.get_ai_response(question))
                        self.send_message(event.peer_id, f"🧠 {ai_response}")
                    elif any(word in message.lower() for word in ['привет', 'hello', 'hi']):
                        # Простые реакции на обычные сообщения
                        self.send_message(event.peer_id, f"👋 Привет! Я VK Бот с системой рангов. Напиши 'помощь' для списка команд.")
                            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            logger.info("🛑 Бот остановлен")
            input("\n👆 Нажми Enter для выхода...")

if __name__ == "__main__":
    # Создаем и запускаем бота
    try:
        bot = VKBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")
        input("\n👆 Нажми Enter для выхода...")