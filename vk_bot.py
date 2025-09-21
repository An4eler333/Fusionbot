import os
import asyncio
import logging
import json
import re
import time
import sqlite3
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

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

class VKBot:
    """Продвинутый VK бот с ИИ и системой рангов"""
    
    def __init__(self):
        # Получаем токены из переменных окружения
        self.vk_token = os.getenv('VK_TOKEN')
        self.group_id = int(os.getenv('VK_GROUP_ID', 0))
        
        # Проверяем валидность токенов
        self.demo_mode = self._check_tokens_validity()
        
        if self.demo_mode:
            logger.warning("⚠️  ДЕМО РЕЖИМ: VK_TOKEN или VK_GROUP_ID не установлены")
            logger.info("🎭 Бот работает в демонстрационном режиме")
            return
        
        if not self.demo_mode:
            try:
                # Инициализация VK API
                self.vk_session = vk_api.VkApi(token=self.vk_token)
                self.vk = self.vk_session.get_api()
                self.longpoll = VkLongPoll(self.vk_session)
                
                # Проверяем валидность токена через несколько методов
                self._validate_vk_token()
                logger.info("✅ VK токен валиден и API готов к работе")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации VK API: {e}")
                logger.warning("⚠️  Переход в демо-режим из-за недействительного токена")
                logger.info("💡 Проверьте токен в файле ТОКЕНЫ.env")
                self.demo_mode = True
        
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
    
    def _check_tokens_validity(self) -> bool:
        """Проверка валидности токенов"""
        # Проверяем наличие токенов
        if not self.vk_token or not self.group_id:
            logger.warning("⚠️  Токены не установлены")
            return True
        
        # Быстрая проверка формата токена
        if not self.vk_token.startswith('vk1.a.'):
            logger.warning("⚠️  Неверный формат VK токена")
            return True
        
        # Пробуем инициализировать VK API для проверки
        try:
            test_session = vk_api.VkApi(token=self.vk_token)
            test_vk = test_session.get_api()
            # Для токенов групп users.get может возвращать пустой список
            # Проверяем через groups.getById
            test_vk.groups.getById(group_id=self.group_id)
            logger.info("✅ Токены валидны")
            return False
        except Exception as e:
            logger.warning(f"⚠️  Токен недействителен: {e}")
            return True
    
    def _validate_vk_token(self):
        """Валидация VK токена через несколько методов"""
        try:
            # Метод 1: Проверка через users.get
            user_info = self.vk.users.get()
            if user_info and len(user_info) > 0:
                logger.info(f"👤 Токен принадлежит пользователю: {user_info[0]['first_name']} {user_info[0]['last_name']}")
            else:
                logger.warning("⚠️  Не удалось получить информацию о пользователе")
            
            # Метод 2: Проверка через groups.getById
            try:
                group_info = self.vk.groups.getById(group_id=self.group_id)
                if group_info and len(group_info) > 0:
                    logger.info(f"🏢 Группа: {group_info[0]['name']}")
                else:
                    logger.warning("⚠️  Не удалось получить информацию о группе")
            except Exception as e:
                logger.warning(f"⚠️  Не удалось получить информацию о группе: {e}")
            
            # Метод 3: Проверка прав на сообщения
            try:
                # Пробуем получить информацию о сообщениях
                self.vk.messages.getConversations(count=1)
                logger.info("💬 Права на работу с сообщениями подтверждены")
            except Exception as e:
                logger.warning(f"⚠️  Ограничения на работу с сообщениями: {e}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка валидации токена: {e}")
            raise
    
    def send_message(self, peer_id: int, message: str, keyboard: Optional[str] = None):
        """Отправка сообщения в ВК"""
        if self.demo_mode:
            logger.info(f"🎭 ДЕМО: Сообщение в чат {peer_id}: {message}")
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
    
    def _register_user_and_add_experience(self, user_id: int, peer_id: int):
        """Регистрация пользователя и начисление опыта"""
        try:
            # Получаем информацию о пользователе из VK
            if not self.demo_mode:
                user_info = self.vk.users.get(user_ids=user_id)[0]
            else:
                # Демо данные
                user_info = {
                    'first_name': f'Пользователь{user_id}',
                    'last_name': 'Демо'
                }
            
            # Создаем или обновляем пользователя
            user_data = db.create_or_update_user(user_id, user_info)
            
            if user_data:
                # Начисляем опыт за сообщение
                experience_gain = random.randint(1, 3)
                self._add_experience(user_id, experience_gain)
                
        except Exception as e:
            logger.error(f"Ошибка регистрации пользователя {user_id}: {e}")
    
    def _add_experience(self, user_id: int, amount: int):
        """Добавить опыт пользователю"""
        try:
            with sqlite3.connect(db.db_path) as conn:
                # Получаем текущий опыт
                cursor = conn.cursor()
                cursor.execute("SELECT experience, rank_level FROM users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                
                if result:
                    current_exp, current_rank = result
                    new_exp = current_exp + amount
                    
                    # Проверяем повышение ранга
                    new_rank = self._calculate_rank(new_exp)
                    
                    # Обновляем данные
                    cursor.execute(
                        "UPDATE users SET experience = ?, rank_level = ?, messages_count = messages_count + 1 WHERE user_id = ?",
                        (new_exp, new_rank, user_id)
                    )
                    
                    # Если ранг повысился
                    if new_rank > current_rank:
                        rank_info = db.get_rank_info(new_rank)
                        logger.info(f"🎉 Пользователь {user_id} повысил ранг до {rank_info['name']}")
                        
        except Exception as e:
            logger.error(f"Ошибка начисления опыта: {e}")
    
    def _calculate_rank(self, experience: int) -> int:
        """Вычислить ранг на основе опыта"""
        if experience < 10:
            return 1
        elif experience < 25:
            return 2
        elif experience < 50:
            return 3
        elif experience < 100:
            return 4
        elif experience < 200:
            return 5
        elif experience < 350:
            return 6
        elif experience < 500:
            return 7
        elif experience < 750:
            return 8
        elif experience < 1000:
            return 9
        else:
            return 10

    # Основной метод запуска бота
    def run(self):
        """Запуск бота с обработкой ошибок"""
        logger.info("🚀 Запуск VK Бота...")
        
        if self.demo_mode:
            logger.info("🎭 Демонстрационный режим активен")
            logger.info("📝 Для полной работы установите VK_TOKEN и VK_GROUP_ID")
            logger.info("🎮 Симуляция работы бота...")
            logger.info("⏸️  Нажмите Ctrl+C для остановки")
            
            # Демо цикл с симуляцией сообщений
            try:
                demo_messages = [
                    ("2000000001", "привет"),
                    ("2000000001", "помощь"),
                    ("2000000001", "тест"),
                    ("2000000001", "ии как дела?"),
                    ("2000000002", "hello"),
                    ("2000000001", "спасибо")
                ]
                
                for i, (peer_id, message) in enumerate(demo_messages):
                    time.sleep(3)
                    logger.info(f"📨 Получено сообщение от {peer_id}: {message}")
                    
                    # Обработка сообщения
                    message_lower = message.lower()
                    
                    if message_lower in ['помощь', 'help']:
                        help_text = """🤖 VK Бот Fusionbot v6.0

📋 Доступные команды:
• помощь - эта справка
• тест - тестовое сообщение
• ии [вопрос] - поговорить с ИИ
• шутка - получить шутку
• история - короткая история
• комплимент - получить комплимент
• топ - топ участников чата
• ранг - узнать свой ранг
• статистика - статистика бота

🎯 Система рангов: от Новичка до Космоса!
💬 Работаем только в беседах"""
                        self.send_message(int(peer_id), help_text)
                    elif message_lower in ['тест', 'test']:
                        self.send_message(int(peer_id), f"✅ Тест пройден! Бот работает нормально.\nВремя: {datetime.now().strftime('%H:%M:%S')}")
                    elif message_lower.startswith('ии ') and len(message) > 3:
                        question = message[3:].strip()
                        ai_response = asyncio.run(ai_system.get_ai_response(question))
                        self.send_message(int(peer_id), f"🧠 {ai_response}")
                    elif message_lower in ['шутка', 'joke']:
                        joke = asyncio.run(ai_system.generate_joke())
                        self.send_message(int(peer_id), f"😂 {joke}")
                    elif message_lower in ['история', 'story']:
                        story = asyncio.run(ai_system.generate_story())
                        self.send_message(int(peer_id), f"📚 {story}")
                    elif message_lower in ['комплимент', 'compliment']:
                        compliment = ai_system._generate_local_compliment()
                        self.send_message(int(peer_id), f"💎 {compliment}")
                    elif message_lower in ['статистика', 'stats']:
                        uptime = datetime.now() - self.start_time
                        stats_text = f"""📊 Статистика бота:
⏰ Время работы: {str(uptime).split('.')[0]}
📨 Обработано сообщений: {self.messages_processed}
💾 База данных: SQLite
🧠 ИИ: Groq API + локальные ответы
🎯 Режим: Демо"""
                        self.send_message(int(peer_id), stats_text)
                    elif any(word in message.lower() for word in ['привет', 'hello', 'hi']):
                        self.send_message(int(peer_id), f"👋 Привет! Я VK Бот с системой рангов. Напиши 'помощь' для списка команд.")
                
                # Продолжаем демо
                while True:
                    time.sleep(10)
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
                    # Работаем с беседами (peer_id > 2000000000) и личными сообщениями
                    # Но приоритет отдаем беседам
                    if event.peer_id <= 2000000000:
                        logger.info(f"📱 Личное сообщение от {event.user_id}: {event.text}")
                        # Можно обрабатывать личные сообщения, но с ограничениями
                        # Пока пропускаем для безопасности
                        continue
                        
                    # Простая обработка сообщений
                    message = event.text.strip()
                    message_lower = message.lower()
                    
                    # Регистрируем пользователя и начисляем опыт
                    self._register_user_and_add_experience(event.user_id, event.peer_id)
                    
                    # Увеличиваем счетчик обработанных сообщений
                    self.messages_processed += 1
                    
                    # Обработка команд без слешей
                    if message_lower in ['помощь', 'help']:
                        help_text = """🤖 VK Бот Fusionbot v6.0

📋 Доступные команды:
• помощь - эта справка
• тест - тестовое сообщение
• ии [вопрос] - поговорить с ИИ
• шутка - получить шутку
• история - короткая история
• комплимент - получить комплимент
• топ - топ участников чата
• ранг - узнать свой ранг
• статистика - статистика бота

🎯 Система рангов: от Новичка до Космоса!
💬 Работаем только в беседах"""
                        self.send_message(event.peer_id, help_text)
                        
                    elif message_lower in ['тест', 'test']:
                        self.send_message(event.peer_id, f"✅ Тест пройден! Бот работает нормально.\nВремя: {datetime.now().strftime('%H:%M:%S')}")
                        
                    elif message_lower.startswith('ии ') and len(message) > 3:
                        # ИИ ответ
                        question = message[3:].strip()
                        ai_response = asyncio.run(ai_system.get_ai_response(question))
                        self.send_message(event.peer_id, f"🧠 {ai_response}")
                        
                    elif message_lower in ['шутка', 'joke']:
                        # Генерация шутки
                        joke = asyncio.run(ai_system.generate_joke())
                        self.send_message(event.peer_id, f"😂 {joke}")
                        
                    elif message_lower in ['история', 'story']:
                        # Генерация истории
                        story = asyncio.run(ai_system.generate_story())
                        self.send_message(event.peer_id, f"📚 {story}")
                        
                    elif message_lower in ['комплимент', 'compliment']:
                        # Генерация комплимента
                        compliment = ai_system._generate_local_compliment()
                        self.send_message(event.peer_id, f"💎 {compliment}")
                        
                    elif message_lower in ['топ', 'top']:
                        # Топ пользователей
                        top_users = db.get_top_users(5)
                        if top_users:
                            top_text = "🏆 Топ участников чата:\n\n"
                            for i, user in enumerate(top_users, 1):
                                rank_info = db.get_rank_info(user['rank_level'])
                                top_text += f"{i}. {rank_info['emoji']} {user['first_name']} {user['last_name']} - {user['experience']} опыта\n"
                            self.send_message(event.peer_id, top_text)
                        else:
                            self.send_message(event.peer_id, "📊 Пока нет данных о пользователях")
                            
                    elif message_lower in ['ранг', 'rank']:
                        # Информация о ранге пользователя
                        user_data = db.get_user(event.user_id)
                        if user_data:
                            rank_info = db.get_rank_info(user_data['rank_level'])
                            rank_text = f"🎖️ Твой ранг: {rank_info['name']}\n"
                            rank_text += f"📊 Опыт: {user_data['experience']}\n"
                            rank_text += f"💬 Сообщений: {user_data['messages_count']}"
                            self.send_message(event.peer_id, rank_text)
                        else:
                            self.send_message(event.peer_id, "👤 Ты еще не зарегистрирован в системе рангов")
                            
                    elif message_lower in ['статистика', 'stats']:
                        # Статистика бота
                        uptime = datetime.now() - self.start_time
                        stats_text = f"""📊 Статистика бота:
⏰ Время работы: {str(uptime).split('.')[0]}
📨 Обработано сообщений: {self.messages_processed}
💾 База данных: SQLite
🧠 ИИ: Groq API + локальные ответы
🎯 Режим: {'Демо' if self.demo_mode else 'Продакшн'}"""
                        self.send_message(event.peer_id, stats_text)
                        
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