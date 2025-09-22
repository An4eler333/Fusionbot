#!/usr/bin/env python3
"""
VK Бот - ЧИСТАЯ версия для работы в беседах
Использует Bots Long Poll и OpenRouter ИИ
"""
import os
import asyncio
import logging
import time
import random
import requests
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv

from database import db
from ai_system import ai_system
from console_admin import console_admin
from moderation_system import ModerationSystem

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

class VKBotClean:
    """VK Бот с чистой архитектурой для бесед"""
    
    def __init__(self):
        # Получаем токены из переменных окружения
        self.vk_token = os.getenv('VK_TOKEN')
        self.group_id = int(os.getenv('VK_GROUP_ID', 0))
        
        # Проверяем валидность токенов
        if not self.vk_token or not self.group_id:
            logger.error("❌ Токены не установлены")
            raise ValueError("Токены VK не найдены в переменных окружения")
        
        # Инициализируем Long Poll для групп
        self._init_group_longpoll()
        
        # Инициализируем систему модерации
        self.moderation = ModerationSystem(self.vk_token, self.group_id)
        
        # Статистика
        self.start_time = datetime.now()
        self.messages_processed = 0
        self._last_send_time = 0.0
        
        logger.info(f"🤖 VK Бот инициализирован. ID группы: {self.group_id}")
        logger.info(f"🎯 Работаем в беседах через Bots Long Poll")
        logger.info(f"🧠 ИИ система: OpenRouter")
        logger.info(f"💾 База данных: SQLite")
    
    def _init_group_longpoll(self):
        """Инициализация Group Long Poll"""
        try:
            # Получаем настройки Long Poll для группы
            response = requests.get(
                'https://api.vk.com/method/groups.getLongPollServer',
                params={
                    'group_id': self.group_id,
                    'access_token': self.vk_token,
                    'v': '5.199'
                }
            )
            
            data = response.json()
            if 'response' in data:
                self.longpoll_server = data['response']['server']
                self.longpoll_key = data['response']['key']
                self.longpoll_ts = data['response']['ts']
                logger.info("✅ Group Long Poll инициализирован")
                logger.info(f"🔄 Сервер: {self.longpoll_server}")
                logger.info(f"🔑 Ключ: {self.longpoll_key[:20]}...")
                logger.info(f"⏰ TS: {self.longpoll_ts}")
            else:
                logger.error(f"❌ Ошибка инициализации Long Poll: {data}")
                raise Exception("Не удалось инициализировать Long Poll")
                
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Long Poll: {e}")
            raise
    
    def is_vk_group_admin(self, user_id: int) -> bool:
        """Проверить, является ли пользователь администратором VK группы"""
        try:
            response = requests.get(
                'https://api.vk.com/method/groups.getMembers',
                params={
                    'group_id': self.group_id,
                    'filter': 'managers',
                    'access_token': self.vk_token,
                    'v': '5.199'
                }
            )
            
            data = response.json()
            if 'response' in data and 'items' in data['response']:
                admin_ids = data['response']['items']
                return user_id in admin_ids
            
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка проверки админа VK группы: {e}")
            return False
    
    def get_user_permissions(self, user_id: int, peer_id: int) -> Dict:
        """Получить права пользователя (VK админ + ранг в боте)"""
        permissions = {
            'is_vk_admin': False,
            'is_bot_admin': False,
            'rank_level': 1,
            'rank_name': '🥉 Новичок',
            'permissions': ['chat']
        }
        
        try:
            # Проверяем VK группу админа
            permissions['is_vk_admin'] = self.is_vk_group_admin(user_id)
            
            # Если VK админ - автоматически максимальные права
            if permissions['is_vk_admin']:
                permissions['is_bot_admin'] = True
                permissions['rank_level'] = 10
                permissions['rank_name'] = '🚀 Космос'
                permissions['permissions'] = [
                    'chat', 'voice', 'reactions', 'jokes', 'games', 
                    'mentions', 'moderate', 'warn', 'mute', 'kick', 'ban'
                ]
                return permissions
            
            # Проверяем ранг в боте
            user_data = db.get_user(user_id)
            if user_data:
                rank_info = db.get_rank_info(user_data.get('rank_level', 1))
                permissions['rank_level'] = user_data.get('rank_level', 1)
                permissions['rank_name'] = rank_info['name']
                permissions['permissions'] = rank_info['permissions']
            
            # Проверяем админа в конкретной беседе
            chat_id = peer_id - 2000000000
            if db.is_admin(user_id, chat_id):
                permissions['is_bot_admin'] = True
                # Админы беседы получают права 8+ ранга
                if permissions['rank_level'] < 8:
                    permissions['rank_level'] = 8
                    permissions['rank_name'] = '👑 Король'
                    permissions['permissions'] = [
                        'chat', 'voice', 'reactions', 'jokes', 'games', 
                        'mentions', 'moderate', 'warn', 'mute'
                    ]
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения прав пользователя: {e}")
        
        return permissions
    
    def send_message(self, peer_id: int, message: str):
        """Отправка сообщения в беседу"""
        try:
            # Rate limiting: не чаще 1 сообщения в 3 секунды
            elapsed = time.time() - self._last_send_time
            if elapsed < 3.0:
                time.sleep(max(0.0, 3.0 - elapsed))

            # Ограничиваем длину сообщения (VK лимит ~4096 символов)
            if len(message) > 4000:
                message = message[:4000] + "..."
                logger.warning(f"⚠️ Сообщение обрезано до 4000 символов")
            response = requests.get(
                'https://api.vk.com/method/messages.send',
                params={
                    'peer_id': peer_id,
                    'message': message,
                    'access_token': self.vk_token,
                    'v': '5.199',
                    'random_id': int(time.time() * 1000)
                }
            )
            
            # Проверяем статус ответа
            if response.status_code != 200:
                logger.error(f"❌ HTTP ошибка: {response.status_code}")
                return False
                
            try:
                data = response.json()
                if 'response' in data:
                    logger.info(f"✅ Сообщение отправлено в {peer_id}")
                    self._last_send_time = time.time()
                    return True
                elif 'error' in data:
                    logger.error(f"❌ VK API ошибка: {data['error']}")
                    self._last_send_time = time.time()
                    return False
                else:
                    logger.error(f"❌ Неожиданный ответ VK API: {data}")
                    self._last_send_time = time.time()
                    return False
            except ValueError as e:
                logger.error(f"❌ Ошибка парсинга JSON: {e}, ответ: {response.text[:200]}")
                self._last_send_time = time.time()
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
    
    def process_message(self, message_data: dict):
        """Обработка сообщения из Long Poll"""
        try:
            # Извлекаем данные сообщения
            user_id = message_data.get('from_id', 0)
            peer_id = message_data.get('peer_id', 0)
            text = message_data.get('text', '')
            timestamp = message_data.get('date', 0)
            
            # Логируем получение сообщения
            logger.info(f"📨 ПОЛУЧЕНО СООБЩЕНИЕ:")
            logger.info(f"   От пользователя: {user_id}")
            logger.info(f"   В чат: {peer_id}")
            logger.info(f"   Текст: '{text}'")
            logger.info(f"   Время: {datetime.fromtimestamp(timestamp)}")
            
            # Определяем тип чата
            if peer_id > 2000000000:
                chat_type = "🗣️ БЕСЕДА"
                chat_id = peer_id - 2000000000
                logger.info(f"   ✅ ТИП: {chat_type} (внутренний ID: {chat_id})")
            else:
                chat_type = "👤 ЛИЧНЫЕ СООБЩЕНИЯ"
                logger.info(f"   ✅ ТИП: {chat_type}")
            
            # Проверяем статус пользователя
            user_status = self.moderation.check_user_status(user_id)
            if user_status["status"] != "ok":
                self.send_message(peer_id, user_status["message"])
                return
            
            # Регистрируем пользователя
            user_info = {"first_name": "Пользователь", "last_name": "VK"}
            db.create_or_update_user(user_id, user_info)
            
            # Добавляем опыт за активность
            db.add_experience(user_id, 1)
            
            # Обновляем ранг
            if db.update_rank(user_id):
                user_rank = db.get_user_rank(user_id)
                self.send_message(peer_id, f"🎉 Поздравляем! Вы получили новый ранг: {user_rank['rank']}")
            
            # Обрабатываем команды
            self.handle_commands(text, user_id, peer_id, chat_type)
            
            # Увеличиваем счетчик сообщений
            self.messages_processed += 1
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения: {e}")
    
    def handle_commands(self, text: str, user_id: int, peer_id: int, chat_type: str):
        """Обработка команд бота"""
        message_lower = text.lower().strip()
        
        try:
            if message_lower in ['тест', 'test']:
                response = f"✅ Тест пройден! Бот работает в беседах!\nВремя: {datetime.now().strftime('%H:%M:%S')}\nТип: {chat_type}\nID: {peer_id}"
                self.send_message(peer_id, response)
                
            elif message_lower in ['помощь', 'help', 'команды']:
                help_text = """🤖 **Fusionbot v6.1 - Команды:**

**🧠 ИИ команды (OpenRouter):**
• `ии [вопрос]` - Задать вопрос ИИ
• `шутка` - Получить шутку
• `история` - Случайная история
• `комплимент` - Получить комплимент
• `время` - Узнать время
• `как дела` - Спросить о настроении
• `расскажи о себе` - Узнать о боте

**📊 Ранги и опыт:**
• `ранг` - Ваш ранг и опыт
• `топ` - Топ пользователей
• `статус` - Ваш статус

**🎮 Развлечения:**
• `викторина` - Начать викторину
• `угадай число` - Игра с числами
• `орёл или решка` - Подбросить монетку

**📊 Информация:**
• `статистика` - Статистика бота
• `тест` - Проверка работы

**🔧 Модерация (для админов):**
• `кик [@пользователь]` - Исключить из беседы
• `мут [@пользователь] [время]` - Замутить
• `бан [@пользователь] [причина]` - Забанить
• `варн [@пользователь] [причина]` - Предупреждение
• `размут [@пользователь]` - Размутить
• `разбан [@пользователь]` - Разбанить

**ℹ️ Справка:**
• `админ` - Админские команды
• `ранги` - Информация о рангах

**👑 VK админы группы автоматически получают максимальные права!**"""
                self.send_message(peer_id, help_text)
                
            elif message_lower.startswith('ии ') and len(text) > 3:
                question = text[3:].strip()
                logger.info(f"🧠 Обрабатываем ИИ запрос: {question}")
                ai_response = asyncio.run(ai_system.get_ai_response(question, "chat", user_id, peer_id))
                self.send_message(peer_id, f"🧠 {ai_response}")
                
            elif message_lower in ['шутка', 'joke']:
                joke = asyncio.run(ai_system.get_ai_response("Расскажи смешную шутку или анекдот", "joke", user_id, peer_id))
                self.send_message(peer_id, f"😂 {joke}")
                
            elif message_lower in ['история', 'story']:
                story = asyncio.run(ai_system.get_ai_response("Расскажи короткую интересную историю", "story", user_id, peer_id))
                self.send_message(peer_id, f"📖 {story}")
                
            elif message_lower in ['комплимент', 'compliment']:
                compliment = asyncio.run(ai_system.get_ai_response("Сделай искренний комплимент", "compliment", user_id, peer_id))
                self.send_message(peer_id, f"💝 {compliment}")
                
            elif message_lower in ['время', 'time']:
                time_response = asyncio.run(ai_system.get_ai_response("Скажи текущее время", "chat", user_id, peer_id))
                self.send_message(peer_id, f"⏰ {time_response}")
                
            elif message_lower in ['как дела', 'how are you']:
                mood_response = asyncio.run(ai_system.get_ai_response("Как дела? Расскажи о своем настроении", "chat", user_id, peer_id))
                self.send_message(peer_id, f"😊 {mood_response}")
                
            elif message_lower in ['расскажи о себе', 'about you']:
                about_response = asyncio.run(ai_system.get_ai_response("Расскажи о себе", "chat", user_id, peer_id))
                self.send_message(peer_id, f"🤖 {about_response}")
                
            elif message_lower in ['ранг', 'rank']:
                user_perms = self.get_user_permissions(user_id, peer_id)
                user_rank = db.get_user_rank(user_id)
                next_exp = user_rank.get('next_level_exp', 0)
                exp_to_next = next_exp - user_rank['experience'] if next_exp > 0 else 0
                
                admin_status = ""
                if user_perms['is_vk_admin']:
                    admin_status = "\n👑 **VK Администратор группы**"
                elif user_perms['is_bot_admin']:
                    admin_status = "\n🔧 **Администратор беседы**"
                
                rank_info = f"""📊 **Ваш ранг: {user_perms['rank_name']}**
💎 Опыт: {user_rank['experience']}
🏆 Уровень: {user_rank['level']}
🎯 До следующего уровня: {exp_to_next} опыта
🔑 Права: {', '.join(user_perms['permissions'])}{admin_status}"""
                self.send_message(peer_id, rank_info)
                
            elif message_lower in ['топ', 'top']:
                top_users = db.get_top_users(10)
                if top_users:
                    top_text = "🏆 **Топ пользователей по опыту:**\n\n"
                    for i, user in enumerate(top_users, 1):
                        user_rank = db.get_user_rank(user['user_id'])
                        top_text += f"{i}. {user_rank['rank']} - {user['experience']} опыта\n"
                    self.send_message(peer_id, top_text)
                else:
                    self.send_message(peer_id, "❌ Нет данных для топа")
                    
            elif message_lower in ['статус', 'status']:
                user_status = self.moderation.check_user_status(user_id)
                user_rank = db.get_user_rank(user_id)
                warnings = db.get_warnings(user_id)
                
                status_text = f"""📊 **Ваш статус:**
{user_status['message']}

📈 **Ранг:** {user_rank['rank']}
💎 **Опыт:** {user_rank['experience']}
⚠️ **Предупреждения:** {warnings}/5"""
                self.send_message(peer_id, status_text)
                
            elif message_lower in ['ранги', 'ranks']:
                ranks_text = """🏆 **Система рангов:**

🥉 **Новичок** (0+ опыта) - Базовые права
🏃 **Активный** (100+ опыта) - Голосовые сообщения
💬 **Болтун** (300+ опыта) - Реакции
🎭 **Шутник** (600+ опыта) - Шутки
🎯 **Меткий** (1000+ опыта) - Игры
⭐ **Звезда** (1500+ опыта) - Упоминания
🔥 **Легенда** (2500+ опыта) - Модерация
👑 **Король** (4000+ опыта) - Предупреждения
💎 **Алмаз** (6000+ опыта) - Мут
🚀 **Космос** (10000+ опыта) - Кик и бан

💡 **Как получить опыт:**
• Сообщения: +1 за каждое
• Админские действия: +3-20
• Активность: +1-5"""
                self.send_message(peer_id, ranks_text)
                
            elif message_lower in ['викторина', 'quiz']:
                questions = [
                    {"q": "Какая столица России?", "a": "москва", "options": ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург"]},
                    {"q": "Сколько планет в Солнечной системе?", "a": "8", "options": ["7", "8", "9", "10"]},
                    {"q": "Кто написал 'Войну и мир'?", "a": "толстой", "options": ["Толстой", "Достоевский", "Пушкин", "Чехов"]},
                    {"q": "Какая самая большая планета?", "a": "юпитер", "options": ["Земля", "Юпитер", "Сатурн", "Нептун"]},
                    {"q": "В каком году был основан VK?", "a": "2006", "options": ["2004", "2005", "2006", "2007"]}
                ]
                question = random.choice(questions)
                quiz_text = f"🎯 **Викторина:**\n\n{question['q']}\n\n"
                for i, option in enumerate(question['options'], 1):
                    quiz_text += f"{i}. {option}\n"
                quiz_text += "\nОтветьте номером варианта!"
                self.send_message(peer_id, quiz_text)
                
            elif message_lower in ['угадай число', 'guess']:
                number = random.randint(1, 100)
                self.send_message(peer_id, f"🎲 **Угадай число от 1 до 100!**\n\nЯ загадал число. Попробуйте угадать! (Напишите число)")
                
            elif message_lower in ['орёл или решка', 'монетка', 'coin']:
                result = random.choice(['орёл', 'решка'])
                self.send_message(peer_id, f"🪙 **Подбрасываю монетку...**\n\n🎯 Выпал: **{result.upper()}**!")
                
            elif message_lower in ['статистика', 'stats']:
                uptime = datetime.now() - self.start_time
                stats_text = f"""📊 Статистика бота:
⏰ Время работы: {str(uptime).split('.')[0]}
📨 Обработано сообщений: {self.messages_processed}
🎯 Тип чата: {chat_type}
💬 ID чата: {peer_id}
🔧 Режим: Bots Long Poll

🤖 ИИ система: OpenRouter
🚫 Локальные fallback отключены"""
                self.send_message(peer_id, stats_text)
                
            elif message_lower.startswith('кик ') and len(text) > 4:
                # Проверяем права на кик
                user_perms = self.get_user_permissions(user_id, peer_id)
                if 'kick' not in user_perms['permissions']:
                    self.send_message(peer_id, f"❌ Недостаточно прав для кика. Ваш ранг: {user_perms['rank_name']}")
                    return
                
                # Парсим команду кика
                parts = text.split()
                if len(parts) >= 2:
                    target_user = self._parse_user_mention(parts[1])
                    if target_user:
                        result = self.moderation.kick_user(peer_id, target_user, user_id)
                        self.send_message(peer_id, result['message'])
                    else:
                        self.send_message(peer_id, "❌ Не удалось найти пользователя. Используйте @упоминание")
                else:
                    self.send_message(peer_id, "❌ Использование: `кик @пользователь`")
                    
            elif message_lower.startswith('мут ') and len(text) > 4:
                # Проверяем права на мут
                user_perms = self.get_user_permissions(user_id, peer_id)
                if 'mute' not in user_perms['permissions']:
                    self.send_message(peer_id, f"❌ Недостаточно прав для мута. Ваш ранг: {user_perms['rank_name']}")
                    return
                
                # Парсим команду мута
                parts = text.split()
                if len(parts) >= 3:
                    target_user = self._parse_user_mention(parts[1])
                    try:
                        duration = int(parts[2])
                        reason = ' '.join(parts[3:]) if len(parts) > 3 else ""
                        if target_user:
                            result = self.moderation.mute_user(peer_id, target_user, user_id, duration, reason)
                            self.send_message(peer_id, result['message'])
                        else:
                            self.send_message(peer_id, "❌ Не удалось найти пользователя. Используйте @упоминание")
                    except ValueError:
                        self.send_message(peer_id, "❌ Время должно быть числом в минутах")
                else:
                    self.send_message(peer_id, "❌ Использование: `мут @пользователь [время_в_минутах] [причина]`")
                    
            elif message_lower.startswith('бан ') and len(text) > 4:
                # Проверяем права на бан
                user_perms = self.get_user_permissions(user_id, peer_id)
                if 'ban' not in user_perms['permissions']:
                    self.send_message(peer_id, f"❌ Недостаточно прав для бана. Ваш ранг: {user_perms['rank_name']}")
                    return
                
                # Парсим команду бана
                parts = text.split()
                if len(parts) >= 2:
                    target_user = self._parse_user_mention(parts[1])
                    reason = ' '.join(parts[2:]) if len(parts) > 2 else ""
                    if target_user:
                        result = self.moderation.ban_user(peer_id, target_user, user_id, reason)
                        self.send_message(peer_id, result['message'])
                    else:
                        self.send_message(peer_id, "❌ Не удалось найти пользователя. Используйте @упоминание")
                else:
                    self.send_message(peer_id, "❌ Использование: `бан @пользователь [причина]`")
                    
            elif message_lower.startswith('варн ') and len(text) > 5:
                # Проверяем права на предупреждение
                user_perms = self.get_user_permissions(user_id, peer_id)
                if 'warn' not in user_perms['permissions']:
                    self.send_message(peer_id, f"❌ Недостаточно прав для предупреждения. Ваш ранг: {user_perms['rank_name']}")
                    return
                
                # Парсим команду предупреждения
                parts = text.split()
                if len(parts) >= 2:
                    target_user = self._parse_user_mention(parts[1])
                    reason = ' '.join(parts[2:]) if len(parts) > 2 else ""
                    if target_user:
                        result = self.moderation.warn_user(peer_id, target_user, user_id, reason)
                        self.send_message(peer_id, result['message'])
                    else:
                        self.send_message(peer_id, "❌ Не удалось найти пользователя. Используйте @упоминание")
                else:
                    self.send_message(peer_id, "❌ Использование: `варн @пользователь [причина]`")
                    
            elif message_lower.startswith('размут ') and len(text) > 7:
                # Парсим команду размута
                parts = text.split()
                if len(parts) >= 2:
                    target_user = self._parse_user_mention(parts[1])
                    if target_user:
                        if db.unmute_user(target_user):
                            self.send_message(peer_id, f"✅ Пользователь размучен")
                        else:
                            self.send_message(peer_id, "❌ Ошибка при размуте")
                    else:
                        self.send_message(peer_id, "❌ Не удалось найти пользователя. Используйте @упоминание")
                else:
                    self.send_message(peer_id, "❌ Использование: `размут @пользователь`")
                    
            elif message_lower.startswith('разбан ') and len(text) > 7:
                # Парсим команду разбана
                parts = text.split()
                if len(parts) >= 2:
                    target_user = self._parse_user_mention(parts[1])
                    if target_user:
                        if db.unban_user(target_user):
                            self.send_message(peer_id, f"✅ Пользователь разбанен")
                        else:
                            self.send_message(peer_id, "❌ Ошибка при разбане")
                    else:
                        self.send_message(peer_id, "❌ Не удалось найти пользователя. Используйте @упоминание")
                else:
                    self.send_message(peer_id, "❌ Использование: `разбан @пользователь`")
                    
            elif message_lower in ['админ', 'admin']:
                user_perms = self.get_user_permissions(user_id, peer_id)
                
                if not user_perms['is_vk_admin'] and not user_perms['is_bot_admin']:
                    self.send_message(peer_id, f"❌ У вас нет прав администратора. Ваш ранг: {user_perms['rank_name']}")
                    return
                
                admin_type = "VK Администратор группы" if user_perms['is_vk_admin'] else "Администратор беседы"
                admin_text = f"""🔧 **Админские команды** ({admin_type}):

**📊 Статистика:**
• `статистика` - Общая статистика
• `ранг` - Ваш ранг
• `топ` - Топ пользователей

**🧠 ИИ:**
• `ии [вопрос]` - Тест ИИ
• `шутка` - Тест генерации

**🔧 Модерация:**
• `кик @пользователь` - Исключить из беседы
• `мут @пользователь [время]` - Замутить
• `бан @пользователь [причина]` - Забанить
• `варн @пользователь [причина]` - Предупреждение
• `размут @пользователь` - Размутить
• `разбан @пользователь` - Разбанить

**ℹ️ Справка:**
• `тест` - Проверка работы
• `помощь` - Список команд
• `ранги` - Информация о рангах

**🔑 Ваши права:** {', '.join(user_perms['permissions'])}"""
                self.send_message(peer_id, admin_text)
                
            elif any(word in message_lower for word in ['привет', 'hello', 'hi']):
                self.send_message(peer_id, f"👋 Привет! Я VK Бот с ИИ системой. Напиши 'помощь' для списка команд.")
            
            logger.info(f"✅ Сообщение обработано (всего: {self.messages_processed})")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки команды: {e}")
            self.send_message(peer_id, "❌ Произошла ошибка при обработке команды. Попробуйте позже.")
    
    def _parse_user_mention(self, mention: str) -> Optional[int]:
        """Парсинг упоминания пользователя"""
        try:
            # Убираем @ и [id
            if mention.startswith('@'):
                mention = mention[1:]
            if mention.startswith('[id'):
                mention = mention[3:]
            if '|' in mention:
                mention = mention.split('|')[0]
            
            # Пытаемся извлечь ID
            user_id = int(mention)
            return user_id
        except (ValueError, IndexError):
            return None
    
    def run(self):
        """Основной цикл бота"""
        logger.info("🚀 Запуск VK Бота с Bots Long Poll...")
        
        try:
            # Проверяем подключение
            response = requests.get(f"{self.longpoll_server}?act=a_check&key={self.longpoll_key}&ts={self.longpoll_ts}&wait=25")
            if response.status_code == 200:
                logger.info("✅ Подключение к Group Long Poll успешно")
            else:
                logger.error(f"❌ Ошибка подключения: {response.status_code}")
                return
                
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Long Poll: {e}")
            return
        
        logger.info("👂 Начинаем прослушивание сообщений из бесед...")
        logger.info("💡 Напишите 'тест' в беседу где добавлен бот")
        
        while True:
            try:
                # Получаем обновления
                response = requests.get(
                    f"{self.longpoll_server}?act=a_check&key={self.longpoll_key}&ts={self.longpoll_ts}&wait=25"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('ts'):
                        self.longpoll_ts = data['ts']
                    
                    if 'updates' in data:
                        for update in data['updates']:
                            if update.get('type') == 'message_new':
                                self.process_message(update['object']['message'])
                                
                else:
                    logger.error(f"❌ Ошибка Long Poll: {response.status_code}")
                    time.sleep(5)
                    
            except Exception as e:
                logger.error(f"❌ Ошибка в основном цикле: {e}")
                time.sleep(5)

def main():
    """Главная функция"""
    try:
        bot = VKBotClean()
        bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
