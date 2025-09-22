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
            # На Windows файлы БД могут оставаться заблокированными в тестах.
            # Включаем WAL и уменьшенные таймауты, чтобы быстрее освобождались дескрипторы.
            with sqlite3.connect(self.db_path, timeout=0.5, isolation_level=None) as conn:
                conn.execute('PRAGMA journal_mode=WAL;')
                conn.execute('PRAGMA synchronous=OFF;')
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
            1: {"name": "🥉 Новичок", "emoji": "🥉", "exp_required": 0, "permissions": ["chat"]},
            2: {"name": "🏃 Активный", "emoji": "🏃", "exp_required": 100, "permissions": ["chat", "voice"]},
            3: {"name": "💬 Болтун", "emoji": "💬", "exp_required": 300, "permissions": ["chat", "voice", "reactions"]},
            4: {"name": "🎭 Шутник", "emoji": "🎭", "exp_required": 600, "permissions": ["chat", "voice", "reactions", "jokes"]},
            5: {"name": "🎯 Меткий", "emoji": "🎯", "exp_required": 1000, "permissions": ["chat", "voice", "reactions", "jokes", "games"]},
            6: {"name": "⭐ Звезда", "emoji": "⭐", "exp_required": 1500, "permissions": ["chat", "voice", "reactions", "jokes", "games", "mentions"]},
            7: {"name": "🔥 Легенда", "emoji": "🔥", "exp_required": 2500, "permissions": ["chat", "voice", "reactions", "jokes", "games", "mentions", "moderate"]},
            8: {"name": "👑 Король", "emoji": "👑", "exp_required": 4000, "permissions": ["chat", "voice", "reactions", "jokes", "games", "mentions", "moderate", "warn"]},
            9: {"name": "💎 Алмаз", "emoji": "💎", "exp_required": 6000, "permissions": ["chat", "voice", "reactions", "jokes", "games", "mentions", "moderate", "warn", "mute"]},
            10: {"name": "🚀 Космос", "emoji": "🚀", "exp_required": 10000, "permissions": ["chat", "voice", "reactions", "jokes", "games", "mentions", "moderate", "warn", "mute", "kick", "ban"]}
        }
        return ranks.get(rank_level, {"name": "🥉 Новичок", "emoji": "🥉", "exp_required": 0, "permissions": ["chat"]})
    
    def add_experience(self, user_id: int, exp: int):
        """Добавить опыт пользователю"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE users SET experience = experience + ? WHERE user_id = ?", (exp, user_id))
        except Exception as e:
            logger.error(f"Ошибка добавления опыта: {e}")
    
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
    
    def get_user_rank(self, user_id: int) -> Dict:
        """Получить ранг пользователя"""
        try:
            user = self.get_user(user_id)
            if not user:
                return {"rank": "🥉 Новичок", "level": 1, "experience": 0}
            
            exp = user.get('experience', 0)
            level = 1
            
            # Определяем уровень по опыту
            for rank_level in range(10, 0, -1):
                rank_info = self.get_rank_info(rank_level)
                if exp >= rank_info['exp_required']:
                    level = rank_level
                    break
            
            rank_info = self.get_rank_info(level)
            return {
                "rank": rank_info['name'],
                "level": level,
                "experience": exp,
                "next_level_exp": self.get_rank_info(level + 1)['exp_required'] if level < 10 else 0,
                "permissions": rank_info['permissions']
            }
        except Exception as e:
            logger.error(f"Ошибка получения ранга: {e}")
            return {"rank": "🥉 Новичок", "level": 1, "experience": 0}
    
    def update_rank(self, user_id: int):
        """Обновить ранг пользователя на основе опыта"""
        try:
            user = self.get_user(user_id)
            if not user:
                return
            
            exp = user.get('experience', 0)
            new_level = 1
            
            # Определяем новый уровень
            for rank_level in range(10, 0, -1):
                rank_info = self.get_rank_info(rank_level)
                if exp >= rank_info['exp_required']:
                    new_level = rank_level
                    break
            
            # Обновляем уровень если изменился
            if new_level != user.get('rank_level', 1):
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("UPDATE users SET rank_level = ? WHERE user_id = ?", (new_level, user_id))
                logger.info(f"Пользователь {user_id} получил новый ранг: {self.get_rank_info(new_level)['name']}")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка обновления ранга: {e}")
            return False
    
    def mute_user(self, user_id: int, duration_minutes: int):
        """Замутить пользователя"""
        try:
            mute_until = datetime.now().timestamp() + (duration_minutes * 60)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE users SET mute_until = ? WHERE user_id = ?", (str(mute_until), user_id))
            logger.info(f"Пользователь {user_id} замучен на {duration_minutes} минут")
            return True
        except Exception as e:
            logger.error(f"Ошибка мута: {e}")
            return False
    
    def unmute_user(self, user_id: int):
        """Размутить пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE users SET mute_until = NULL WHERE user_id = ?", (user_id,))
            logger.info(f"Пользователь {user_id} размучен")
            return True
        except Exception as e:
            logger.error(f"Ошибка размута: {e}")
            return False
    
    def is_muted(self, user_id: int) -> bool:
        """Проверить замучен ли пользователь"""
        try:
            user = self.get_user(user_id)
            if not user or not user.get('mute_until'):
                return False
            
            mute_until = float(user['mute_until'])
            if datetime.now().timestamp() > mute_until:
                self.unmute_user(user_id)
                return False
            return True
        except Exception as e:
            logger.error(f"Ошибка проверки мута: {e}")
            return False
    
    def ban_user(self, user_id: int):
        """Забанить пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (user_id,))
            logger.info(f"Пользователь {user_id} забанен")
            return True
        except Exception as e:
            logger.error(f"Ошибка бана: {e}")
            return False
    
    def unban_user(self, user_id: int):
        """Разбанить пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (user_id,))
            logger.info(f"Пользователь {user_id} разбанен")
            return True
        except Exception as e:
            logger.error(f"Ошибка разбана: {e}")
            return False
    
    def is_banned(self, user_id: int) -> bool:
        """Проверить забанен ли пользователь"""
        try:
            user = self.get_user(user_id)
            return user and user.get('banned', 0) == 1
        except Exception as e:
            logger.error(f"Ошибка проверки бана: {e}")
            return False
    
    def add_warning(self, user_id: int):
        """Добавить предупреждение"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id = ?", (user_id,))
            logger.info(f"Пользователю {user_id} добавлено предупреждение")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления предупреждения: {e}")
            return False
    
    def get_warnings(self, user_id: int) -> int:
        """Получить количество предупреждений"""
        try:
            user = self.get_user(user_id)
            return user.get('warnings', 0) if user else 0
        except Exception as e:
            logger.error(f"Ошибка получения предупреждений: {e}")
            return 0

# Глобальный экземпляр базы данных
db = DatabaseManager()