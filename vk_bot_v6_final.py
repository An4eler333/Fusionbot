#!/usr/bin/env python3
"""
VK Бот - ПРАВИЛЬНАЯ версия для работы в беседах
Использует Bots Long Poll вместо User Long Poll
"""
import os
import asyncio
import logging
import json
import time
import sqlite3
import random
import requests
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv

from database import db
from ai_system import ai_system
from console_admin import console_admin

# Загружаем переменные окружения
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

class VKBotCorrect:
    """VK Бот с правильной архитектурой для бесед"""
    
    def __init__(self):
        # Получаем токены из переменных окружения
        self.vk_token = os.getenv('VK_TOKEN')
        self.group_id = int(os.getenv('VK_GROUP_ID', 0))
        
        # Проверяем валидность токенов
        if not self.vk_token or not self.group_id:
            logger.error("❌ Токены не установлены")
            return
        
        self.api_url = "https://api.vk.com/method/"
        self.api_version = "5.199"
        
        # Настройки Long Poll для групп
        self.longpoll_server = None
        self.longpoll_key = None
        self.longpoll_ts = None
        
        # Статистика
        self.start_time = datetime.now()
        self.messages_processed = 0
        
        # Инициализируем Long Poll для групп
        self._init_group_longpoll()
        
        logger.info(f"🤖 VK Бот инициализирован. ID группы: {self.group_id}")
        logger.info(f"🎯 Работаем в беседах через Bots Long Poll")
        logger.info(f"🧠 ИИ система: Groq API + локальные ответы")
        logger.info(f"💾 База данных: SQLite")
    
    def _init_group_longpoll(self):
        """Инициализация Group Long Poll"""
        try:
            # Получаем сервер Long Poll для группы
            response = self._api_request('groups.getLongPollServer', {
                'group_id': self.group_id
            })
            
            if response and 'response' in response:
                data = response['response']
                self.longpoll_server = data['server']
                self.longpoll_key = data['key']
                self.longpoll_ts = data['ts']
                
                logger.info("✅ Group Long Poll инициализирован")
                logger.info(f"🔄 Сервер: {self.longpoll_server}")
                logger.info(f"🔑 Ключ: {self.longpoll_key[:20]}...")
                logger.info(f"⏰ TS: {self.longpoll_ts}")
            else:
                logger.error("❌ Не удалось получить Long Poll сервер")
                
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Long Poll: {e}")
    
    def _api_request(self, method: str, params: Dict) -> Optional[Dict]:
        """Выполнение API запроса"""
        try:
            params.update({
                'access_token': self.vk_token,
                'v': self.api_version
            })
            
            response = requests.get(f"{self.api_url}{method}", params=params)
            return response.json()
            
        except Exception as e:
            logger.error(f"❌ Ошибка API запроса {method}: {e}")
            return None
    
    def send_message(self, peer_id: int, message: str):
        """Отправка сообщения"""
        try:
            params = {
                'peer_id': peer_id,
                'message': message,
                'random_id': random.randint(1, 2147483647)
            }
            
            response = self._api_request('messages.send', params)
            
            if response and 'response' in response:
                logger.info(f"✅ Сообщение отправлено в {peer_id}")
            else:
                error = response.get('error', {}) if response else {}
                logger.error(f"❌ Ошибка отправки: {error}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
    
    def _get_longpoll_updates(self):
        """Получение обновлений через Group Long Poll"""
        if not all([self.longpoll_server, self.longpoll_key, self.longpoll_ts]):
            logger.error("❌ Long Poll не инициализирован")
            return None
        
        try:
            params = {
                'act': 'a_check',
                'key': self.longpoll_key,
                'ts': self.longpoll_ts,
                'wait': 25
            }
            
            response = requests.get(self.longpoll_server, params=params, timeout=30)
            data = response.json()
            
            if 'ts' in data:
                self.longpoll_ts = data['ts']
            
            return data.get('updates', [])
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения обновлений: {e}")
            return None
    
    def _process_message(self, update):
        """Обработка сообщения"""
        try:
            # Парсим обновление
            event_type = update.get('type')
            
            if event_type == 'message_new':
                message_data = update.get('object', {}).get('message', {})
                
                user_id = message_data.get('from_id')
                peer_id = message_data.get('peer_id')
                text = message_data.get('text', '').strip()
                date = message_data.get('date', 0)
                
                logger.info(f"📨 ПОЛУЧЕНО СООБЩЕНИЕ:")
                logger.info(f"   От пользователя: {user_id}")
                logger.info(f"   В чат: {peer_id}")
                logger.info(f"   Текст: '{text}'")
                logger.info(f"   Время: {datetime.fromtimestamp(date)}")
                
                # Определяем тип чата
                if peer_id > 2000000000:
                    chat_type = "🗣️ БЕСЕДА"
                    chat_id = peer_id - 2000000000
                    logger.info(f"   ✅ ТИП: {chat_type} (внутренний ID: {chat_id})")
                else:
                    chat_type = "👤 ЛИЧНОЕ СООБЩЕНИЕ"
                    logger.info(f"   ✅ ТИП: {chat_type}")
                
                # Обрабатываем команды
                message_lower = text.lower()
                self.messages_processed += 1
                
                if message_lower in ['тест', 'test']:
                    response = f"✅ Тест пройден! Бот работает в беседах!\nВремя: {datetime.now().strftime('%H:%M:%S')}\nТип: {chat_type}\nID: {peer_id}"
                    self.send_message(peer_id, response)
                    
                elif message_lower in ['помощь', 'help']:
                    help_text = """🤖 VK Бот Fusionbot v6.0

📋 Доступные команды:
• помощь - эта справка
• тест - тестовое сообщение
• ии [вопрос] - поговорить с ИИ
• шутка - получить шутку
• статистика - статистика бота

🎯 Система рангов: от Новичка до Космоса!
💬 Работаем в беседах через Bots Long Poll"""
                    self.send_message(peer_id, help_text)
                    
                elif message_lower.startswith('ии ') and len(text) > 3:
                    question = text[3:].strip()
                    logger.info(f"🧠 Обрабатываем ИИ запрос: {question}")
                    ai_response = asyncio.run(ai_system.get_ai_response(question))
                    self.send_message(peer_id, f"🧠 {ai_response}")
                    
                elif message_lower in ['шутка', 'joke']:
                    joke = asyncio.run(ai_system.generate_joke())
                    self.send_message(peer_id, f"😂 {joke}")
                    
                elif message_lower in ['статистика', 'stats']:
                    uptime = datetime.now() - self.start_time
                    stats_text = f"""📊 Статистика бота:
⏰ Время работы: {str(uptime).split('.')[0]}
📨 Обработано сообщений: {self.messages_processed}
🎯 Тип чата: {chat_type}
💬 ID чата: {peer_id}
🔧 Режим: Bots Long Poll"""
                    self.send_message(peer_id, stats_text)
                    
                elif any(word in message_lower for word in ['привет', 'hello', 'hi']):
                    self.send_message(peer_id, f"👋 Привет! Я VK Бот с системой рангов. Напиши 'помощь' для списка команд.")
                
                logger.info(f"✅ Сообщение обработано (всего: {self.messages_processed})")
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения: {e}")
    
    def run(self):
        """Запуск бота"""
        logger.info("🚀 Запуск VK Бота с Bots Long Poll...")
        
        if not all([self.longpoll_server, self.longpoll_key, self.longpoll_ts]):
            logger.error("❌ Long Poll не инициализирован")
            return
        
        logger.info("✅ Подключение к Group Long Poll успешно")
        logger.info("👂 Начинаем прослушивание сообщений из бесед...")
        logger.info("💡 Напишите 'тест' в беседу где добавлен бот")
        
        try:
            while True:
                updates = self._get_longpoll_updates()
                
                if updates:
                    for update in updates:
                        self._process_message(update)
                elif updates is None:
                    # Ошибка - переинициализируем Long Poll
                    logger.warning("⚠️  Переинициализация Long Poll...")
                    self._init_group_longpoll()
                    time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Получен сигнал остановки")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            logger.info("🛑 Бот остановлен")

if __name__ == "__main__":
    try:
        bot = VKBotCorrect()
        bot.run()
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")
        input("\n👆 Нажми Enter для выхода...")
