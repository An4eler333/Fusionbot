"""
Система искусственного интеллекта для VK Bot Fusionbot v6.x
Поддерживает OpenRouter и Hugging Face API
"""

import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

class AISystem:
    """Система искусственного интеллекта"""
    
    def __init__(self):
        self.huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.polza_api_keys = [
            os.getenv('POLZA_API_KEY'),
            os.getenv('POLZA_API_KEY_2')
        ]
        # Убираем None значения
        self.polza_api_keys = [key for key in self.polza_api_keys if key]
        
        logger.info(f"🧠 ИИ система инициализирована (Hugging Face + Polza AI: {len(self.polza_api_keys)} ключей + OpenRouter)")
    
    async def get_ai_response(self, message: str, context: str = "chat", user_id: int = 0, peer_id: int = 0) -> str:
        """Получить ответ от ИИ с модерацией.

        Порядок: Hugging Face → Polza AI → OpenRouter.
        Без локальных fallback ответов.
        """
        try:
            # Проверка модерации
            from moderation import moderation_system
            moderation_result = moderation_system.check_content(message, user_id, peer_id)
            if not moderation_result['allowed']:
                return moderation_result['response']

            # ПРИОРИТЕТ 1 - Hugging Face API (бесплатный)
            if self.huggingface_api_key:
                response = await self._call_huggingface(message, context)
                if response and response.strip():
                    logger.info(f"✅ Hugging Face ответ получен: {response[:100]}...")
                    return response
                else:
                    logger.warning("⚠️ Hugging Face не дал ответ, пробуем Polza AI...")

            # ПРИОРИТЕТ 2 - Polza AI (российский сервис)
            if self.polza_api_keys:
                response = await self._call_polza(message, context)
                if response and response.strip():
                    logger.info(f"✅ Polza AI ответ получен: {response[:100]}...")
                    return response
                else:
                    logger.warning("⚠️ Polza AI не дал ответ, пробуем OpenRouter...")

            # ПРИОРИТЕТ 3 - OpenRouter API (работает в России)
            if self.openrouter_api_key:
                response = await self._call_openrouter(message, context)
                if response and response.strip():
                    logger.info(f"✅ OpenRouter ответ получен: {response[:100]}...")
                    return response

            # Если все ИИ недоступны - возвращаем ошибку
            logger.error("❌ Все ИИ сервисы недоступны")
            return "🤖 Извините, ИИ сервисы временно недоступны. Попробуйте позже."

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
    
    async def _call_polza(self, message: str, context: str) -> Optional[str]:
        """Вызов Polza AI API (российский сервис) с автоматическим переключением ключей"""
        system_prompt = self._get_system_prompt(context)
        
        # Пробуем каждый ключ Polza AI
        for i, api_key in enumerate(self.polza_api_keys, 1):
            try:
                logger.info(f"🔄 Пробуем Polza AI (ключ {i}/{len(self.polza_api_keys)}): {message[:50]}...")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "https://api.polza.ai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                            "User-Agent": "VK-Bot-Fusionbot/1.0"
                        },
                        json={
                            "model": "gpt-3.5-turbo",  # Вернемся к базовой модели Polza AI
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
                        if 'choices' in data and len(data['choices']) > 0:
                            ai_response = data['choices'][0]['message']['content']
                            if ai_response and ai_response.strip():
                                # Очищаем токены модели
                                ai_response = self._clean_ai_response(ai_response)
                                logger.info(f"✅ Polza AI ответ получен (ключ {i}): {ai_response[:100]}...")
                                return ai_response
                            else:
                                logger.warning(f"⚠️ Polza AI ключ {i} вернул пустой ответ")
                        else:
                            logger.warning(f"⚠️ Polza AI ключ {i} вернул некорректный формат ответа")
                    else:
                        logger.warning(f"⚠️ Polza AI ключ {i} ошибка: {response.status_code} - {response.text}")
                        continue
                        
            except Exception as e:
                logger.warning(f"⚠️ Polza AI ключ {i} исключение: {e}")
                continue
        
        logger.error("❌ Все ключи Polza AI недоступны")
        return None
    
    async def _call_huggingface(self, message: str, context: str) -> Optional[str]:
        """Вызов Hugging Face API"""
        try:
            logger.info(f"🔄 Пробуем Hugging Face API: {message[:50]}...")
            
            system_prompt = self._get_system_prompt(context)
            full_prompt = f"{system_prompt}\n\nПользователь: {message}\n\nАссистент:"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill",
                    headers={
                        "Authorization": f"Bearer {self.huggingface_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "inputs": message,  # BlenderBot работает лучше с простым вводом
                        "parameters": {
                            "max_length": 150,
                            "temperature": 0.8,
                            "do_sample": True,
                            "top_p": 0.9
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        ai_response = data[0].get('generated_text', '')
                        # Убираем исходное сообщение из ответа BlenderBot
                        if message in ai_response:
                            ai_response = ai_response.replace(message, '').strip()
                        if ai_response and ai_response.strip():
                            # Очищаем токены модели
                            ai_response = self._clean_ai_response(ai_response)
                            logger.info(f"✅ Hugging Face ответ получен: {ai_response[:100]}...")
                            return ai_response
                        else:
                            logger.warning("⚠️ Hugging Face вернул пустой ответ")
                            return None
                    else:
                        logger.warning("⚠️ Hugging Face вернул некорректный формат ответа")
                        return None
                else:
                    logger.error(f"❌ Ошибка Hugging Face API: {response.status_code} - {response.text}")
                    return None
                            
        except Exception as e:
            logger.error(f"❌ Ошибка Hugging Face API: {e}")
            # Пробуем альтернативную модель
            return await self._call_huggingface_alternative(message, context)
    
    async def _call_huggingface_alternative(self, message: str, context: str) -> Optional[str]:
        """Альтернативный вызов Hugging Face с другой моделью"""
        try:
            logger.info(f"🔄 Пробуем альтернативную модель Hugging Face: {message[:50]}...")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api-inference.huggingface.co/models/microsoft/DialoGPT-small",
                    headers={
                        "Authorization": f"Bearer {self.huggingface_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "inputs": message,
                        "parameters": {
                            "max_length": 100,
                            "temperature": 0.9,
                            "do_sample": True
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        ai_response = data[0].get('generated_text', '')
                        if ai_response and ai_response.strip():
                            # Убираем исходное сообщение
                            if message in ai_response:
                                ai_response = ai_response.replace(message, '').strip()
                            ai_response = self._clean_ai_response(ai_response)
                            logger.info(f"✅ Hugging Face альтернативная модель ответ: {ai_response[:100]}...")
                            return ai_response
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка альтернативной модели Hugging Face: {e}")
            return None
    
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