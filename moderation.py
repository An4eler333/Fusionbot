"""
Система модерации для VK Бота
"""
import logging
from datetime import datetime
from typing import List, Dict

# Настройка логирования модерации
moderation_logger = logging.getLogger('moderation')
moderation_handler = logging.FileHandler('moderation.log', encoding='utf-8')
moderation_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
moderation_logger.addHandler(moderation_handler)
moderation_logger.setLevel(logging.INFO)

class ContentModeration:
    """Система модерации контента (переименовано для избежания коллизий имён)."""
    
    def __init__(self):
        # Списки запрещенных слов по категориям
        self.inappropriate_words = [
            'хуй', 'блядь', 'пизда', 'ебал', 'сука', 'мудак', 'дебил', 'дибил',
            'говно', 'срать', 'жопа', 'пидор', 'гей', 'лесби', 'рот ебал'
        ]
        
        self.hate_speech = [
            'убить', 'смерть', 'ненавижу', 'убью', 'сдохни',
            'фашист', 'нацист', 'расист'
        ]
        
        self.spam_patterns = [
            'реклама', 'купить', 'продать', 'скидка', 'акция',
            'заработок', 'деньги легко', 'без вложений'
        ]
        
        self.blocked_count = 0
        
    def check_content(self, message: str, user_id: int, peer_id: int) -> Dict:
        """Проверка контента на соответствие правилам"""
        message_lower = message.lower()
        
        result = {
            'allowed': True,
            'reason': None,
            'category': None,
            'response': None
        }
        
        # Проверка на неподходящий контент
        if any(word in message_lower for word in self.inappropriate_words):
            result.update({
                'allowed': False,
                'reason': 'inappropriate_language',
                'category': 'Неподходящий язык',
                'response': "Извини, не могу обсуждать такие темы. Давай поговорим о чём-то другом! Например, спроси меня про науку, технологии или попроси шутку"
            })
            
        # Проверка на язык ненависти
        elif any(word in message_lower for word in self.hate_speech):
            result.update({
                'allowed': False,
                'reason': 'hate_speech',
                'category': 'Язык ненависти',
                'response': "Я не могу поддерживать такие высказывания. Давай общаться дружелюбно! Спроси меня что-то интересное"
            })
            
        # Проверка на спам
        elif any(word in message_lower for word in self.spam_patterns):
            result.update({
                'allowed': False,
                'reason': 'spam',
                'category': 'Спам/реклама',
                'response': "Я не обрабатываю рекламные сообщения. Давай поговорим о чём-то интересном!"
            })
        
        # Логирование заблокированного контента
        if not result['allowed']:
            self.blocked_count += 1
            moderation_logger.info(f"BLOCKED - Category: {result['category']}, Reason: {result['reason']}, User: {user_id}, Chat: {peer_id}")
        
        return result
    
    def get_stats(self) -> Dict:
        """Статистика модерации"""
        return {
            'blocked_messages': self.blocked_count,
            'categories': ['Неподходящий язык', 'Язык ненависти', 'Спам/реклама']
        }

# Глобальный экземпляр системы модерации
moderation_system = ContentModeration()
