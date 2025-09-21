"""
Система базы данных для VK Бота
"""
import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Менеджер базы данных SQLite"""
    
    def __init__(self, db_path: str = "vk_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        first_name TEXT,
                        last_name TEXT,
                        experience INTEGER DEFAULT 0,
                        rank_level INTEGER DEFAULT 1,
                        messages_count INTEGER DEFAULT 0,
                        voice_messages INTEGER DEFAULT 0,
                        mentions_count INTEGER DEFAULT 0,
                        reactions_count INTEGER DEFAULT 0,
                        warnings INTEGER DEFAULT 0,
                        banned INTEGER DEFAULT 0,
                        mute_until TEXT,
                        join_date TEXT,
                        last_activity TEXT
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS chat_admins (
                        user_id INTEGER,
                        chat_id INTEGER,
                        is_owner INTEGER DEFAULT 0,
                        PRIMARY KEY (user_id, chat_id)
                    )
                ''')
                
                logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить пользователя по ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя {user_id}: {e}")
            return None
    
    def create_or_update_user(self, user_id: int, user_info: Dict) -> Dict:
        """Создать или обновить пользователя"""
        try:
            current_time = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, first_name, last_name, join_date, last_activity)
                    VALUES (?, ?, ?, COALESCE((SELECT join_date FROM users WHERE user_id = ?), ?), ?)
                ''', (user_id, user_info.get('first_name', ''), user_info.get('last_name', ''), 
                      user_id, current_time, current_time))
                
            return self.get_user(user_id)
        except Exception as e:
            logger.error(f"Ошибка создания пользователя {user_id}: {e}")
            return None
    
    def is_admin(self, user_id: int, chat_id: int) -> bool:
        """Проверить админа"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM chat_admins WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Ошибка проверки админа: {e}")
            return False
    
    def set_admin(self, user_id: int, chat_id: int, is_owner: bool = False):
        """Установить админа"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT OR REPLACE INTO chat_admins VALUES (?, ?, ?)", 
                           (user_id, chat_id, 1 if is_owner else 0))
        except Exception as e:
            logger.error(f"Ошибка установки админа: {e}")
    
    def get_rank_info(self, rank_level: int) -> Dict:
        """Получить информацию о ранге"""
        ranks = {
            1: {"name": "🥉 Новичок", "emoji": "🥉"},
            2: {"name": "🏃 Активный", "emoji": "🏃"},
            3: {"name": "💬 Болтун", "emoji": "💬"},
            4: {"name": "🎭 Шутник", "emoji": "🎭"},
            5: {"name": "🎯 Меткий", "emoji": "🎯"},
            6: {"name": "⭐ Звезда", "emoji": "⭐"},
            7: {"name": "🔥 Легенда", "emoji": "🔥"},
            8: {"name": "👑 Король", "emoji": "👑"},
            9: {"name": "💎 Алмаз", "emoji": "💎"},
            10: {"name": "🚀 Космос", "emoji": "🚀"}
        }
        return ranks.get(rank_level, {"name": "🥉 Новичок", "emoji": "🥉"})
    
    def get_top_users(self, limit: int = 10) -> List[Dict]:
        """Получить топ пользователей"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users ORDER BY experience DESC LIMIT ?", (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения топа: {e}")
            return []

# Глобальный экземпляр базы данных
db = DatabaseManager()