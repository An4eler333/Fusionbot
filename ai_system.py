"""
Система ИИ для VK Бота с поддержкой российских сервисов
"""
import os
import logging
import asyncio
import random
import aiohttp
import json
from typing import Optional

logger = logging.getLogger(__name__)

class AISystem:
    """Система искусственного интеллекта"""
    
    def __init__(self):
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
        logger.info("🧠 ИИ система инициализирована")
    
    async def get_ai_response(self, message: str, context: str = "chat") -> str:
        """Получить ответ от ИИ с fallback системой"""
        try:
            # Пробуем Groq API (если есть ключ)
            if self.groq_api_key:
                response = await self._call_groq(message, context)
                if response:
                    return response
            
            # Fallback - локальные ответы
            return self._get_local_response(message, context)
            
        except Exception as e:
            logger.error(f"Ошибка ИИ: {e}")
            return self._get_local_response(message, context)
    
    async def _call_groq(self, message: str, context: str) -> Optional[str]:
        """Вызов Groq API"""
        if not self.groq_api_key:
            logger.info("Groq API ключ не установлен")
            return None
            
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.groq_api_key}',
                    'Content-Type': 'application/json'
                }
                
                # Формируем промпт в зависимости от контекста
                system_prompt = self._get_system_prompt(context)
                
                data = {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "model": "llama3-8b-8192",
                    "temperature": 0.7,
                    "max_tokens": 500
                }
                
                async with session.post(
                    'https://api.groq.com/openai/v1/chat/completions',
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        ai_response = result['choices'][0]['message']['content']
                        logger.info("✅ Groq API ответ получен")
                        return ai_response
                    else:
                        logger.warning(f"Groq API ошибка: {response.status}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.warning("Groq API таймаут")
            return None
        except Exception as e:
            logger.error(f"Ошибка Groq API: {e}")
            return None
    
    def _get_system_prompt(self, context: str) -> str:
        """Получить системный промпт для контекста"""
        prompts = {
            "chat": "Ты дружелюбный помощник в VK чате. Отвечай кратко, весело и по-русски. Используй эмодзи.",
            "joke": "Ты мастер шуток. Придумай смешную шутку на русском языке с эмодзи.",
            "story": "Ты рассказчик. Создай короткую интересную историю на русском языке с эмодзи.",
            "compliment": "Ты мастер комплиментов. Скажи что-то приятное и ободряющее на русском языке с эмодзи."
        }
        return prompts.get(context, prompts["chat"])
    
    def _get_local_response(self, message: str, context: str) -> str:
        """Локальные умные ответы"""
        message_lower = message.lower()
        
        # Ответы на приветствия
        if any(word in message_lower for word in ['привет', 'hello', 'hi', 'здравствуй']):
            responses = [
                "👋 Привет! Как дела?",
                "🤖 Привет! Я готов помочь!",
                "✋ Здравствуй! Что интересного?",
                "😊 Привет! Рад тебя видеть!"
            ]
            return random.choice(responses)
        
        # Ответы на вопросы
        if '?' in message or any(word in message_lower for word in ['что', 'как', 'когда', 'где', 'почему']):
            responses = [
                "🤔 Интересный вопрос! Дай подумать...",
                "💭 Хороший вопрос! К сожалению, я пока учусь отвечать на сложные вопросы.",
                "🧠 Я думаю над этим! Попробуй переформулировать вопрос.",
                "💡 Интересно! Может, кто-то из участников беседы знает ответ?"
            ]
            return random.choice(responses)
        
        # Реакция на благодарности
        if any(word in message_lower for word in ['спасибо', 'thanks', 'thx', 'благодарю']):
            responses = [
                "😊 Пожалуйста! Всегда рад помочь!",
                "🤗 Не за что! Обращайся еще!",
                "✨ Всегда пожалуйста!",
                "😄 Рад был помочь!"
            ]
            return random.choice(responses)
        
        # Контекстные ответы
        if context == "joke":
            return self._generate_local_joke()
        elif context == "story":
            return self._generate_local_story()
        elif context == "compliment":
            return self._generate_local_compliment()
        
        # Обычные ответы
        default_responses = [
            "🤖 Понимаю! Интересная мысль.",
            "💭 Хм, любопытно!",
            "👍 Согласен с тобой!",
            "🎯 Точное наблюдение!",
            "🔥 Круто сказано!",
            "💡 А вот это идея!",
            "😎 Стильно!",
            "⚡ Энергично!"
        ]
        return random.choice(default_responses)
    
    async def generate_joke(self) -> str:
        """Генерация шутки"""
        return self._generate_local_joke()
    
    def _generate_local_joke(self) -> str:
        """Локальные шутки"""
        jokes = [
            "😂 Почему программисты не любят природу?\n— Слишком много багов!",
            "🤖 Встречаются два робота:\n— Как дела?\n— 01001000 01101001!\n— Понятно, плохо дела...",
            "😄 Что общего между программистом и волшебником?\n— Оба превращают кофе в код!",
            "🎭 Заходит программист в бар и говорит:\n— Дайте мне пиво!\n— Какое?\n— Да любое, я не привередливый!\n— А вот коды у вас привередливые!",
            "💻 Почему у программистов всегда грязная клавиатура?\n— Потому что они постоянно баги давят!",
            "🐛 Программист приходит домой поздно.\n— Где был?\n— На работе баг ловил.\n— Поймал?\n— Нет, но завёл ещё троих!",
        ]
        return random.choice(jokes)
    
    async def generate_story(self, theme: str = "") -> str:
        """Генерация истории"""
        return self._generate_local_story(theme)
    
    def _generate_local_story(self, theme: str = "") -> str:
        """Локальные истории"""
        if theme:
            return f"📚 **История на тему '{theme}'**\n\nЭто была удивительная история о {theme.lower()}. Главный герой отправился в невероятное приключение, где встретил множество интересных персонажей. В конце все проблемы решились, и все жили долго и счастливо! ✨"
        
        stories = [
            "📚 **Сказка о храбром разработчике**\n\nЖил-был программист, который не боялся никаких багов. Однажды он встретил Дракона Синего Экрана, но победил его силой чистого кода! 🐉⚔️",
            "🚀 **Космическая история**\n\nВ далекой галактике робот-исследователь обнаружил планету, где все говорили на языке программирования. Оказалось, что это была планета разработчиков! 🌟",
            "🏰 **Легенда о потерянном алгоритме**\n\nДревние мудрецы спрятали идеальный алгоритм в загадочном лабиринте. Тот, кто его найдет, получит власть над всеми багами мира! 🗝️",
        ]
        return random.choice(stories)
    
    def _generate_local_compliment(self) -> str:
        """Локальные комплименты"""
        compliments = [
            "🌟 Ты просто звезда этой беседы!",
            "🎯 У тебя отличное чувство юмора!",
            "🔥 Ты всегда знаешь, что сказать!",
            "⚡ Твоя энергия заряжает всех вокруг!",
            "💎 Ты драгоценный участник нашей команды!",
            "🎨 У тебя творческий подход к жизни!",
            "🧠 Твой ум просто восхищает!",
            "💫 Ты делаешь этот мир лучше!"
        ]
        return random.choice(compliments)

# Глобальный экземпляр ИИ системы
ai_system = AISystem()