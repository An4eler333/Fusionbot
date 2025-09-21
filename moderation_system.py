"""
Расширенная система модерации с VK API
"""
import requests
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database import db

logger = logging.getLogger(__name__)

class ModerationSystem:
    """Система модерации с VK API интеграцией"""
    
    def __init__(self, vk_token: str, group_id: int):
        self.vk_token = vk_token
        self.group_id = group_id
        
    def kick_user(self, peer_id: int, user_id: int, admin_id: int) -> Dict:
        """Кикнуть пользователя из беседы"""
        try:
            # Проверяем права админа
            if not self._check_admin_permissions(admin_id, peer_id, "kick"):
                return {"success": False, "message": "❌ У вас нет прав для кика пользователей"}
            
            # Проверяем что пользователь не админ
            if db.is_admin(user_id, peer_id - 2000000000):
                return {"success": False, "message": "❌ Нельзя кикнуть администратора"}
            
            # Удаляем пользователя из беседы
            response = requests.get(
                'https://api.vk.com/method/messages.removeChatUser',
                params={
                    'chat_id': peer_id - 2000000000,
                    'user_id': user_id,
                    'access_token': self.vk_token,
                    'v': '5.199'
                }
            )
            
            data = response.json()
            if 'response' in data and data['response'] == 1:
                # Очищаем сообщения пользователя
                self._clear_user_messages(peer_id, user_id)
                
                # Добавляем опыт админу
                db.add_experience(admin_id, 10)
                
                logger.info(f"Пользователь {user_id} кикнут из беседы {peer_id} админом {admin_id}")
                return {"success": True, "message": f"✅ Пользователь успешно исключен из беседы"}
            else:
                error_msg = data.get('error', {}).get('error_msg', 'Неизвестная ошибка')
                return {"success": False, "message": f"❌ Ошибка кика: {error_msg}"}
                
        except Exception as e:
            logger.error(f"Ошибка кика пользователя: {e}")
            return {"success": False, "message": "❌ Произошла ошибка при кике пользователя"}
    
    def ban_user(self, peer_id: int, user_id: int, admin_id: int, reason: str = "") -> Dict:
        """Забанить пользователя"""
        try:
            # Проверяем права админа
            if not self._check_admin_permissions(admin_id, peer_id, "ban"):
                return {"success": False, "message": "❌ У вас нет прав для бана пользователей"}
            
            # Проверяем что пользователь не админ
            if db.is_admin(user_id, peer_id - 2000000000):
                return {"success": False, "message": "❌ Нельзя забанить администратора"}
            
            # Баним в базе данных
            if db.ban_user(user_id):
                # Кикаем из беседы
                kick_result = self.kick_user(peer_id, user_id, admin_id)
                if kick_result["success"]:
                    # Добавляем опыт админу
                    db.add_experience(admin_id, 20)
                    
                    logger.info(f"Пользователь {user_id} забанен в беседе {peer_id} админом {admin_id}. Причина: {reason}")
                    return {"success": True, "message": f"✅ Пользователь забанен и исключен из беседы. Причина: {reason}"}
                else:
                    return {"success": True, "message": f"✅ Пользователь забанен (но не удалось исключить из беседы). Причина: {reason}"}
            else:
                return {"success": False, "message": "❌ Ошибка при бане пользователя"}
                
        except Exception as e:
            logger.error(f"Ошибка бана пользователя: {e}")
            return {"success": False, "message": "❌ Произошла ошибка при бане пользователя"}
    
    def mute_user(self, peer_id: int, user_id: int, admin_id: int, duration_minutes: int, reason: str = "") -> Dict:
        """Замутить пользователя"""
        try:
            # Проверяем права админа
            if not self._check_admin_permissions(admin_id, peer_id, "mute"):
                return {"success": False, "message": "❌ У вас нет прав для мута пользователей"}
            
            # Проверяем что пользователь не админ
            if db.is_admin(user_id, peer_id - 2000000000):
                return {"success": False, "message": "❌ Нельзя замутить администратора"}
            
            # Мутим пользователя
            if db.mute_user(user_id, duration_minutes):
                # Добавляем опыт админу
                db.add_experience(admin_id, 5)
                
                logger.info(f"Пользователь {user_id} замучен на {duration_minutes} минут в беседе {peer_id} админом {admin_id}. Причина: {reason}")
                return {"success": True, "message": f"✅ Пользователь замучен на {duration_minutes} минут. Причина: {reason}"}
            else:
                return {"success": False, "message": "❌ Ошибка при муте пользователя"}
                
        except Exception as e:
            logger.error(f"Ошибка мута пользователя: {e}")
            return {"success": False, "message": "❌ Произошла ошибка при муте пользователя"}
    
    def warn_user(self, peer_id: int, user_id: int, admin_id: int, reason: str = "") -> Dict:
        """Выдать предупреждение пользователю"""
        try:
            # Проверяем права админа
            if not self._check_admin_permissions(admin_id, peer_id, "warn"):
                return {"success": False, "message": "❌ У вас нет прав для выдачи предупреждений"}
            
            # Добавляем предупреждение
            if db.add_warning(user_id):
                warnings = db.get_warnings(user_id)
                
                # Добавляем опыт админу
                db.add_experience(admin_id, 3)
                
                # Автоматические действия при накоплении предупреждений
                if warnings >= 3:
                    # Автомут на 30 минут
                    db.mute_user(user_id, 30)
                    logger.info(f"Пользователь {user_id} получил автомута за 3 предупреждения")
                    return {"success": True, "message": f"⚠️ Предупреждение выдано ({warnings}/3). Автомут на 30 минут! Причина: {reason}"}
                elif warnings >= 5:
                    # Автобан
                    ban_result = self.ban_user(peer_id, user_id, admin_id, f"Автобан за {warnings} предупреждений")
                    return {"success": True, "message": f"⚠️ Предупреждение выдано ({warnings}/5). АВТОБАН! Причина: {reason}"}
                else:
                    logger.info(f"Пользователю {user_id} выдано предупреждение в беседе {peer_id} админом {admin_id}. Причина: {reason}")
                    return {"success": True, "message": f"⚠️ Предупреждение выдано ({warnings}/5). Причина: {reason}"}
            else:
                return {"success": False, "message": "❌ Ошибка при выдаче предупреждения"}
                
        except Exception as e:
            logger.error(f"Ошибка выдачи предупреждения: {e}")
            return {"success": False, "message": "❌ Произошла ошибка при выдаче предупреждения"}
    
    def _check_admin_permissions(self, user_id: int, peer_id: int, action: str) -> bool:
        """Проверить права администратора"""
        try:
            # Проверяем в базе данных
            if db.is_admin(user_id, peer_id - 2000000000):
                return True
            
            # Проверяем ранг пользователя
            user_rank = db.get_user_rank(user_id)
            permissions = user_rank.get('permissions', [])
            
            # Проверяем права на действие
            if action == "kick" and "kick" in permissions:
                return True
            elif action == "ban" and "ban" in permissions:
                return True
            elif action == "mute" and "mute" in permissions:
                return True
            elif action == "warn" and "warn" in permissions:
                return True
            elif action == "moderate" and "moderate" in permissions:
                return True
            
            return False
        except Exception as e:
            logger.error(f"Ошибка проверки прав: {e}")
            return False
    
    def _clear_user_messages(self, peer_id: int, user_id: int):
        """Очистить сообщения пользователя (заглушка)"""
        try:
            # VK API не позволяет удалять сообщения других пользователей
            # Это только логирование для статистики
            logger.info(f"Запрос на очистку сообщений пользователя {user_id} в беседе {peer_id}")
        except Exception as e:
            logger.error(f"Ошибка очистки сообщений: {e}")
    
    def check_user_status(self, user_id: int) -> Dict:
        """Проверить статус пользователя"""
        try:
            if db.is_banned(user_id):
                return {"status": "banned", "message": "❌ Вы забанены и не можете использовать бота"}
            elif db.is_muted(user_id):
                user = db.get_user(user_id)
                mute_until = float(user['mute_until'])
                mute_time = datetime.fromtimestamp(mute_until)
                return {"status": "muted", "message": f"🔇 Вы замучены до {mute_time.strftime('%H:%M:%S')}"}
            else:
                return {"status": "ok", "message": "✅ Статус нормальный"}
        except Exception as e:
            logger.error(f"Ошибка проверки статуса: {e}")
            return {"status": "ok", "message": "✅ Статус нормальный"}
