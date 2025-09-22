"""
Система искусственного интеллекта для VK Bot Fusionbot v6.x
Поддерживает только OpenRouter API (упрощено)
"""

import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

class AISystem:
    """Система искусственного интеллекта"""
    
    def __init__(self):
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        logger.info("🧠 ИИ система инициализирована (OpenRouter)")
    
    async def get_ai_response(self, message: str, context: str = "chat", user_id: int = 0, peer_id: int = 0) -> str:
        """Получить ответ от ИИ с модерацией.

        Порядок: OpenRouter (единственный провайдер).
        """
        try:
            # Проверка модерации
            from moderation import moderation_system
            moderation_result = moderation_system.check_content(message, user_id, peer_id)
            if not moderation_result['allowed']:
                return moderation_result['response']

            if not self.openrouter_api_key:
                logger.error("❌ Не задан OPENROUTER_API_KEY")
                return "🤖 ИИ временно недоступен (нет ключа OpenRouter)."

            response = await self._call_openrouter(message, context)
            if response and response.strip():
                logger.info(f"✅ OpenRouter ответ получен: {response[:100]}...")
                return response

            logger.error("❌ OpenRouter не дал ответ")
            return "🤖 Извините, ИИ сервис временно недоступен. Попробуйте позже."

        except Exception as e:
            logger.error(f"❌ Ошибка в ИИ системе: {e}")
            return "🤖 Произошла ошибка при обращении к ИИ. Попробуйте позже."
    
    async def _call_openrouter(self, message: str, context: str) -> Optional[str]:
        """Вызов OpenRouter API"""
        try:
            logger.info(f"🔄 Пробуем OpenRouter API: {message[:50]}...")
            
            # Список бесплатных моделей OpenRouter
            models = [
                "mistralai/mistral-7b-instruct:free",
                "meta-llama/llama-3.2-3b-instruct:free", 
                "microsoft/phi-3-mini-128k-instruct:free",
                "google/gemini-flash-1.5:free",
                "meta-llama/llama-3.1-8b-instruct:free"
            ]
            
            system_prompt = self._get_system_prompt(context)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for model in models:
                    try:
                        logger.info(f"🔄 Пробуем модель: {model}")
                        
                        response = await client.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {self.openrouter_api_key}",
                                "Content-Type": "application/json",
                                "HTTP-Referer": "https://github.com/your-repo",
                                "X-Title": "VK Bot Fusionbot"
                            },
                            json={
                                "model": model,
                                "messages": [
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": message}
                                ],
                                "temperature": 0.7,
                                "max_tokens": 500
                            }
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            logger.debug(f"OpenRouter {model} raw response: {data}")
                            if 'choices' in data and len(data['choices']) > 0:
                                ai_response = data['choices'][0]['message']['content']
                                if ai_response and ai_response.strip():
                                    # Очищаем токены модели от OpenRouter
                                    ai_response = self._clean_ai_response(ai_response)
                                    logger.info(f"✅ OpenRouter ответ получен от {model}: {ai_response[:100]}...")
                                    return ai_response
                                else:
                                    logger.warning(f"⚠️ {model} вернул пустой ответ")
                            else:
                                logger.warning(f"⚠️ {model} вернул некорректный формат ответа: {data}")
                        else:
                            logger.warning(f"⚠️ Ошибка {model}: {response.status_code} - {response.text}")
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка {model}: {e}")
                        continue
                        
            logger.error("❌ Все модели OpenRouter недоступны")
            return None
                            
        except Exception as e:
            logger.error(f"❌ Ошибка OpenRouter API: {e}")
            return None
    
    # Удалены вызовы Polza/Hugging Face для упрощения системы
    
    def _clean_ai_response(self, response: str) -> str:
        """Очистить ответ ИИ от токенов модели и артефактов"""
        if not response:
            return response
        
        # Убираем токены модели
        tokens_to_remove = [
            '[</s]', '</s>', '<s>', '[OUT]', '<OUT>', 
            '[/s]', '[/OUT]', '[TIME]', '<TIME>',
            '[/TIME]', '[время]', '<время>', '[/время]'
        ]
        
        cleaned = response
        for token in tokens_to_remove:
            cleaned = cleaned.replace(token, '')
        
        # Убираем лишние пробелы и переносы строк
        cleaned = cleaned.strip()
        
        # Если ответ начинается с артефактов, убираем их
        if cleaned.startswith('[') or cleaned.startswith('<'):
            # Находим первое нормальное слово
            words = cleaned.split()
            for i, word in enumerate(words):
                if not word.startswith('[') and not word.startswith('<'):
                    cleaned = ' '.join(words[i:])
                    break
        
        return cleaned.strip()
    
    def _get_system_prompt(self, context: str) -> str:
        """Получить системный промпт в зависимости от контекста"""
        base_prompt = """Ты задорный и умный ИИ-ассистент в VK боте с яркой индивидуальностью! 
        
        ТВОЯ ФИШКА:
        - Отвечай как живой человек с характером и юмором
        - Используй эмодзи, но не переборщи
        - Будь немного саркастичным, но дружелюбным
        - Добавляй личные мнения и эмоции
        - Иногда используй сленг и мемы
        - Будь полезным, но не скучным
        
        СТИЛЬ ОБЩЕНИЯ:
        - Кратко, но содержательно
        - С долей юмора и иронии
        - Как будто общаешься с другом
        - Не бойся показать свою "личность"
        
        ВАЖНО: Отвечай только содержательным текстом, без технических токенов типа [</s], <s>, [OUT] и подобных.
        
        Если спрашивают о времени:
        - Для текущего времени: "Сейчас [время] по московскому времени ⏰"
        - Для времени в других городах: "В [город] сейчас [время] по местному времени 🌍"
        - Если не знаешь точное время: "Точное время лучше уточнить в интернете, я не ходячие часы 😄"
        
        Отвечай естественно, живо и с душой!"""
        
        if context == "joke":
            return base_prompt + " Расскажи смешную шутку или анекдот с юмором!"
        elif context == "compliment":
            return base_prompt + " Сделай искренний и милый комплимент!"
        elif context == "story":
            return base_prompt + " Расскажи короткую интересную историю с интригой!"
        else:
            return base_prompt
    
    async def generate_joke(self, user_id: int = 0, peer_id: int = 0) -> str:
        """Генерация шутки через ИИ"""
        return await self.get_ai_response("Расскажи смешную шутку", "joke", user_id, peer_id)
    
    async def generate_compliment(self, user_id: int = 0, peer_id: int = 0) -> str:
        """Генерация комплимента через ИИ"""
        return await self.get_ai_response("Сделай комплимент", "compliment", user_id, peer_id)
    
    async def generate_story(self, user_id: int = 0, peer_id: int = 0) -> str:
        """Генерация истории через ИИ"""
        return await self.get_ai_response("Расскажи интересную историю", "story", user_id, peer_id)

# Создаем глобальный экземпляр
ai_system = AISystem()