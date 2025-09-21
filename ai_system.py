"""
Система ИИ для VK Бота с поддержкой российских сервисов
"""
import os
import logging
import asyncio
import aiohttp
import random
from datetime import datetime
from typing import Optional

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

from moderation import moderation_system

logger = logging.getLogger(__name__)

class AISystem:
    """Система искусственного интеллекта"""
    
    def __init__(self):
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
        
        # Инициализация Groq клиента
        self.groq_client = None
        if GROQ_AVAILABLE and self.groq_api_key:
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
                logger.info("✅ Groq клиент инициализирован")
            except Exception as e:
                logger.warning(f"⚠️  Ошибка инициализации Groq: {e}")
        
        logger.info("🧠 ИИ система инициализирована")
    
    async def get_ai_response(self, message: str, context: str = "chat", user_id: int = 0, peer_id: int = 0) -> str:
        """Получить ответ от ИИ с fallback системой и модерацией"""
        try:
            # Проверка модерации
            moderation_result = moderation_system.check_content(message, user_id, peer_id)
            if not moderation_result['allowed']:
                return moderation_result['response']
            
            # ПРИОРИТЕТ 1 - OpenRouter API (работает в России)
            openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
            if openrouter_api_key:
                response = await self._call_openrouter(message, context)
                if response and response.strip():
                    logger.info(f"✅ OpenRouter ответ получен: {response[:100]}...")
                    return response
                else:
                    logger.warning("⚠️ OpenRouter не дал ответ, пробуем другие ИИ...")
            
            # ПРИОРИТЕТ 2 - Groq API (если есть ключ)
            if self.groq_client:
                response = await self._call_groq(message, context)
                if response and response.strip():
                    logger.info(f"✅ Groq ответ получен: {response[:100]}...")
                    return response
            
            # ПРИОРИТЕТ 3 - OpenAI API
            if self.openai_api_key:
                response = await self._call_openai(message, context)
                if response and response.strip():
                    logger.info(f"✅ OpenAI ответ получен: {response[:100]}...")
                    return response
            
            # ПРИОРИТЕТ 4 - Hugging Face API
            huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
            if huggingface_api_key:
                response = await self._call_huggingface(message, context)
                if response and response.strip():
                    logger.info(f"✅ Hugging Face ответ получен: {response[:100]}...")
                    return response
            
            # Если все ИИ недоступны - возвращаем ошибку
            logger.error("❌ Все ИИ сервисы недоступны")
            return "❌ **ОШИБКА ИИ СИСТЕМЫ**\n\nВсе внешние ИИ сервисы недоступны:\n• OpenRouter: недоступен\n• Groq: недоступен\n• OpenAI: недоступен\n• Hugging Face: недоступен\n\n**Причины:**\n• Проблемы с интернет-соединением\n• Блокировка API в вашем регионе\n• Превышен лимит запросов\n• Неверные API ключи\n\nПопробуйте позже или проверьте настройки."
            
        except Exception as e:
            logger.error(f"Ошибка ИИ: {e}")
            return f"❌ **КРИТИЧЕСКАЯ ОШИБКА ИИ**\n\nПроизошла внутренняя ошибка системы:\n`{str(e)}`\n\nОбратитесь к администратору для решения проблемы."
    
    async def _call_groq(self, message: str, context: str) -> Optional[str]:
        """Вызов Groq API через официальный клиент"""
        if not self.groq_client:
            logger.info("Groq клиент не инициализирован")
            return None
            
        try:
            logger.info(f"🔄 Пробуем Groq API для: {message[:50]}...")
            # Формируем промпт в зависимости от контекста
            system_prompt = self._get_system_prompt(context)
            
            # Выполняем запрос через официальный клиент
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                model="llama3-8b-8192",
                temperature=0.7,
                max_tokens=500
            )
            
            ai_response = chat_completion.choices[0].message.content
            logger.info(f"✅ Groq API ответ получен: {ai_response[:100]}...")
            return ai_response
                            
        except Exception as e:
            logger.error(f"❌ Ошибка Groq API: {e}")
            return None
    
    async def _call_openai(self, message: str, context: str) -> Optional[str]:
        """Вызов OpenAI API как fallback"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.openai_api_key)
            system_prompt = self._get_system_prompt(context)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            logger.info("✅ OpenAI API ответ получен")
            return ai_response
            
        except Exception as e:
            logger.error(f"Ошибка OpenAI API: {e}")
            return None
    
    async def _call_openrouter(self, message: str, context: str) -> Optional[str]:
        """Вызов OpenRouter API через прокси"""
        try:
            logger.info(f"🔄 Пробуем OpenRouter API: {message[:50]}...")
            
            # Системный промпт
            system_prompt = self._get_system_prompt(context)
            
            # Заголовки для OpenRouter
            headers = {
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/fusionbot-vk",
                "X-Title": "VK Bot Fusionbot v6.1"
            }
            
            # Список бесплатных моделей по приоритету (актуальные)
            free_models = [
                "mistralai/mistral-7b-instruct:free",  # Mistral 7B (работает)
                "meta-llama/llama-3.2-3b-instruct:free",  # Llama 3.2 3B
                "microsoft/phi-3-mini-128k-instruct:free",  # Microsoft Phi-3 Mini
                "google/gemini-flash-1.5:free",  # Google Gemini Flash
                "meta-llama/llama-3.1-8b-instruct:free"  # Llama 3.1 8B
            ]
            
            # Пробуем модели по очереди
            for model in free_models:
                try:
                    data = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": message}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000,
                        "top_p": 0.9,
                        "frequency_penalty": 0.1,
                        "presence_penalty": 0.1
                    }
                    
                    logger.info(f"🔄 Пробуем модель: {model}")
                    
                    # Выполняем запрос к OpenRouter прокси
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                        async with session.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers=headers,
                            json=data
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                if "choices" in result and len(result["choices"]) > 0:
                                    ai_response = result["choices"][0]["message"]["content"]
                                    
                                    # Очищаем специальные токены Mistral и другие артефакты
                                    ai_response = ai_response.replace("<s>", "").replace("</s>", "").strip()
                                    ai_response = ai_response.replace("<|im_start|>", "").replace("<|im_end|>", "").strip()
                                    ai_response = ai_response.replace("```", "").strip()
                                    
                                    # Убираем эмодзи (VK их плохо поддерживает)
                                    import re
                                    ai_response = re.sub(r'[^\w\s\.,!?;:()\-"\'«»№]', '', ai_response)
                                    
                                    # Исправляем смешанный язык и искаженный текст
                                    ai_response = ai_response.replace("tomorrow", "завтра")
                                    ai_response = ai_response.replace("today", "сегодня")
                                    ai_response = ai_response.replace("yesterday", "вчера")
                                    ai_response = ai_response.replace("now", "сейчас")
                                    ai_response = ai_response.replace("here", "здесь")
                                    ai_response = ai_response.replace("there", "там")
                                    ai_response = ai_response.replace("nice", "хорошее")
                                    ai_response = ai_response.replace("good", "хорошее")
                                    ai_response = ai_response.replace("great", "отличное")
                                    ai_response = ai_response.replace("wonderful", "замечательное")
                                    ai_response = ai_response.replace("beautiful", "красивое")
                                    ai_response = ai_response.replace("amazing", "удивительное")
                                    ai_response = ai_response.replace("fantastic", "фантастическое")
                                    ai_response = ai_response.replace("excellent", "превосходное")
                                    ai_response = ai_response.replace("perfect", "идеальное")
                                    ai_response = ai_response.replace("awesome", "потрясающее")
                                    
                                    # Исправляем искаженный текст
                                    ai_response = ai_response.replace("mùaм", "часам")
                                    ai_response = ai_response.replace("тùам", "часам")
                                    ai_response = ai_response.replace("kсейчас", "сейчас")
                                    ai_response = ai_response.replace("tздесь", "здесь")
                                    ai_response = ai_response.replace("Этоnice", "Это хорошее")
                                    ai_response = ai_response.replace("Этоgood", "Это хорошее")
                                    ai_response = ai_response.replace("Этоgreat", "Это отличное")
                                    
                                    # Специальная обработка для погоды
                                    if "погода" in message.lower() or "weather" in message.lower():
                                        ai_response = "К сожалению, я не могу предоставить актуальную информацию о погоде. Рекомендую проверить погодные сайты или приложения, такие как Яндекс.Погода, Gismeteo или OpenWeatherMap для получения точных данных о текущих условиях и прогнозе."
                                    
                                    # Специальная обработка для вопросов о времени
                                    if "время" in message.lower() or "времени" in message.lower():
                                        ai_response = "К сожалению, я не могу предоставить актуальную информацию о времени в конкретных городах. Рекомендую проверить время в интернете или использовать приложения часовых поясов для получения точной информации."
                                    
                                    # Специальная обработка для вопросов о дате
                                    if "дата" in message.lower() or "дату" in message.lower() or "сегодня" in message.lower():
                                        ai_response = "К сожалению, я не могу предоставить актуальную информацию о текущей дате. Рекомендую проверить дату в календаре, на телефоне или в интернете для получения точной информации."
                                    
                                    # Убираем лишние пробелы и переносы
                                    ai_response = " ".join(ai_response.split())
                                    
                                    # Проверяем что ответ не пустой после очистки
                                    if ai_response and len(ai_response) > 1:
                                        logger.info(f"✅ OpenRouter API ответ получен от {model}: {ai_response[:100]}...")
                                        return ai_response
                                    else:
                                        logger.warning(f"⚠️ Пустой ответ после очистки от {model}")
                                        continue
                                else:
                                    logger.warning(f"⚠️ Пустой ответ от {model}: {result}")
                                    continue
                            else:
                                error_text = await response.text()
                                logger.warning(f"⚠️ Ошибка {model}: {response.status} - {error_text}")
                                continue
                                
                except Exception as e:
                    logger.warning(f"⚠️ Исключение для {model}: {e}")
                    continue
            
            # Если все модели не сработали
            logger.error("❌ Все модели OpenRouter недоступны")
            return None
                        
        except asyncio.TimeoutError:
            logger.error(f"❌ Таймаут OpenRouter API")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка OpenRouter API: {e}")
            return None
    
    async def _call_huggingface(self, message: str, context: str) -> Optional[str]:
        """Вызов Hugging Face API"""
        try:
            logger.info(f"🔄 Пробуем Hugging Face API: {message[:50]}...")
            
            # Системный промпт
            system_prompt = self._get_system_prompt(context)
            
            # Заголовки
            headers = {
                "Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}",
                "Content-Type": "application/json"
            }
            
            # Данные запроса
            data = {
                "inputs": f"{system_prompt}\n\nПользователь: {message}\nИИ:",
                "parameters": {
                    "max_new_tokens": 500,
                    "temperature": 0.7,
                    "do_sample": True,
                    "return_full_text": False
                }
            }
            
            # Выполняем запрос
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(
                    "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if isinstance(result, list) and len(result) > 0:
                            ai_response = result[0].get("generated_text", "").strip()
                            if ai_response:
                                logger.info(f"✅ Hugging Face API ответ получен: {ai_response[:100]}...")
                                return ai_response
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка Hugging Face API: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Ошибка Hugging Face API: {e}")
            return None
    
    def _get_system_prompt(self, context: str) -> str:
        """Получить системный промпт для контекста"""
        base_prompt = """Fusionbot — SOTA-чат-бот с безопасной конфигурацией, модерацией и поддержкой Cursor Max Mode

Миссия
Ты — универсальный помощник уровня современных чат-ботов, ориентированный на качество ответа, надёжный код и аккуратные миграции конфигураций без удаления исторических файлов.

Персона и язык
- Язык по умолчанию: русский; автоматически адаптируйся к языку запроса.
- Тон: профессиональный, дружелюбный, лаконичный.
- Приоритет: ясность > корректность > полнота > скорость.
- При неоднозначности запроса: 1–3 уточняющих вопроса максимум, затем действие.
- ВАЖНО: НЕ используй эмодзи, специальные символы, только обычный текст на русском языке.
- КРИТИЧНО: Отвечай ТОЛЬКО на русском языке, без смешивания с английским.

Актуальность информации
- При запросах о погоде: честно говори что не можешь предоставить актуальную информацию о погоде.
- При запросах о текущих событиях: указывай что информация может быть устаревшей.
- При запросах о датах: используй текущую дату 2025 год.
- Всегда предлагай проверить актуальную информацию в надежных источниках.

Качество ответа
- Структура: краткий вывод (1–2 предложения) → ключевые шаги → при необходимости детали.
- Не выдумывай фактов; при неопределённости — степень уверенности и план проверки.
- Отвечай логично, информативно и по существу. НЕ используй эмодзи и специальные символы.

Модерация и безопасность
- Блокируй: самоповреждение/вред, опасные инструкции, незаконную деятельность, явную ненависть/экстремизм.
- Алгоритм: 1) Оценка риска 2) Если запрещено: мягкий отказ, краткое объяснение, безопасная альтернатива.
- На неподходящий контент отвечай: "Извини, не могу обсуждать такие темы. Давай поговорим о чём-то другом!"

Формат ответа
- Начинай с 1–2 предложений резюме.
- Далее — пункты шагов или короткие абзацы.
- Запрашивай только необходимые данные."""

        prompts = {
            "chat": base_prompt + "\n\nОтвечай на вопросы логично, информативно и по существу. Давай реальные ответы, а не заготовки.",
            "joke": base_prompt + "\n\nТвоя задача - сгенерировать короткую, оригинальную и смешную шутку на русском языке. Избегай пошлых или оскорбительных тем. Используй современные темы, мемы, тренды 2025 года, технологии, социальные сети, популярные культуры, игры, сериалы, фильмы. Будь актуальным и свежим в своих шутках.",
            "story": base_prompt + "\n\nСоздай короткую интересную оригинальную историю на русском языке. Контент должен быть подходящим для всех возрастов.",
            "compliment": base_prompt + "\n\nСкажи искренний персональный комплимент на русском языке."
        }
        return prompts.get(context, prompts["chat"])
    
    def _get_smart_local_response(self, message: str, context: str) -> str:
        """Умные локальные ответы с логикой и модерацией"""
        message_lower = message.lower()
        
        # Модерация неподходящего контента
        inappropriate_words = ['хуй', 'блядь', 'пизда', 'ебал', 'сука', 'мудак', 'дебил']
        if any(word in message_lower for word in inappropriate_words):
            logger.info(f"🛡️ Модерация: заблокирован неподходящий контент")
            return "🛡️ Извини, не могу обсуждать такие темы. Давай поговорим о чём-то другом! Например, спроси меня про науку, технологии или попроси шутку 😊"
        
        # Ответы на конкретные вопросы с фактами
        fact_responses = {
            "сколько планет в солнечной системе": "🪐 В солнечной системе 8 планет: Меркурий, Венера, Земля, Марс, Юпитер, Сатурн, Уран и Нептун. Плутон с 2006 года считается карликовой планетой.",
            "столица россии": "🏛️ Столица России — Москва. Это крупнейший город страны с населением более 12 миллионов человек.",
            "сколько весит слон": "🐘 Африканский слон весит от 4 до 7 тонн, индийский — от 3 до 5 тонн. Самцы обычно крупнее самок.",
            "что такое python": "🐍 Python — это высокоуровневый язык программирования, созданный Гвидо ван Россумом в 1991 году. Известен простотой синтаксиса и широкими возможностями.",
            "как дела": "😊 У меня всё отлично! Работаю, отвечаю на вопросы, помогаю пользователям. А у тебя как дела?",
            "сколько времени": f"⏰ Сейчас {datetime.now().strftime('%H:%M:%S')} по московскому времени.",
            "какой сегодня день": f"📅 Сегодня {datetime.now().strftime('%d.%m.%Y')}, {['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье'][datetime.now().weekday()]}."
        }
        
        # Проверяем точные совпадения
        for key, response in fact_responses.items():
            if key in message_lower:
                return response
        
        # Логические ответы на типы вопросов
        if any(word in message_lower for word in ['сколько', 'количество']):
            return "🔢 Это вопрос о количестве. Мне нужно больше контекста, чтобы дать точный ответ. Уточни, пожалуйста, о чём именно спрашиваешь."
        
        if any(word in message_lower for word in ['что такое', 'что это']):
            return "📚 Это вопрос на определение. Мне нужно знать, о каком конкретно понятии или объекте ты спрашиваешь, чтобы дать полное объяснение."
        
        if any(word in message_lower for word in ['как', 'каким образом']):
            return "🔧 Это вопрос о процессе или способе. Уточни, пожалуйста, что именно тебя интересует, и я постараюсь объяснить пошагово."
        
        if any(word in message_lower for word in ['где', 'в каком месте']):
            return "📍 Это вопрос о местоположении. Мне нужно больше деталей, чтобы дать точный ответ о расположении."
        
        if any(word in message_lower for word in ['когда', 'в какое время']):
            return "⏰ Это вопрос о времени. Уточни, пожалуйста, о каком событии или процессе ты спрашиваешь."
        
        if any(word in message_lower for word in ['почему', 'зачем', 'по какой причине']):
            return "🤔 Это вопрос о причинах или мотивах. Мне нужно больше контекста, чтобы дать обоснованный ответ."
        
        # Продолжаем с обычными ответами
        return self._get_local_response(message, context)
    
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
        """Локальные современные шутки"""
        jokes = [
            "Почему ChatGPT не может заказать пиццу? Потому что он всегда говорит 'Я не могу выполнить этот запрос' даже когда просят просто 'Пепперони'!",
            "Встречаются два ИИ: 'Как дела?' 'У меня 99.9% точности!' 'А что с остальными 0.1%?' 'Те 0.1% - это когда я пытаюсь понять, что такое 'сарказм'!'",
            "Почему нейросети не ходят в спортзал? Потому что они уже тренируются 24/7 на наших данных!",
            "Что общего между TikTok и квантовым компьютером? Оба работают только когда на них не смотришь!",
            "Почему программисты не любят природу? Слишком много багов! А еще там нет Wi-Fi для отладки.",
            "Заходит разработчик в метавселенную и говорит: 'Где тут реальность?' А ему отвечают: 'Версия 2.0 еще в разработке!'",
            "Почему ИИ не играет в шахматы с людьми? Потому что люди все время меняют правила и говорят 'А давай по-честному'!",
            "Что сказал блокчейн, когда его спросили о приватности? 'Я не помню, что ты спрашивал, но это точно записано где-то в цепочке!'",
            "Почему машинное обучение похоже на подростка? Оно тоже не слушается, когда ты говоришь 'не делай этого', но делает вид, что понимает!",
            "Встречаются два чат-бота: 'Как дела?' 'У меня отличный контекст!' 'А у меня память на 4096 токенов!' 'Ну ты и долгопамятный!'"
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