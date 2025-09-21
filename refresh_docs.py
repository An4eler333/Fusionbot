#!/usr/bin/env python3
"""
Скрипт для обновления документации через Context7
"""
import os
import sys
import json
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Context7Manager:
    """Менеджер для работы с Context7"""
    
    def __init__(self):
        self.config_file = "context7_vk_config.json"
        self.cache_file = "context7_cache.json"
        self.last_update = None
        
    def load_config(self) -> Dict:
        """Загрузка конфигурации Context7"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Файл конфигурации {self.config_file} не найден")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга конфигурации: {e}")
            return {}
    
    def save_cache(self, data: Dict):
        """Сохранение кэша документации"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("Кэш документации сохранен")
        except Exception as e:
            logger.error(f"Ошибка сохранения кэша: {e}")
    
    def load_cache(self) -> Dict:
        """Загрузка кэша документации"""
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.info("Кэш не найден, будет создан новый")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка загрузки кэша: {e}")
            return {}
    
    def check_context7_availability(self) -> bool:
        """Проверка доступности Context7"""
        try:
            result = subprocess.run(
                ["npx", "-y", "@upstash/context7-mcp", "--version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                logger.info("Context7 доступен")
                return True
            else:
                logger.warning(f"Context7 недоступен: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("Таймаут при проверке Context7")
            return False
        except Exception as e:
            logger.error(f"Ошибка проверки Context7: {e}")
            return False
    
    def refresh_vk_api_docs(self) -> Dict:
        """Обновление документации VK API"""
        logger.info("🔄 Обновление документации VK API...")
        
        # Здесь будет логика обновления через Context7
        # Пока что возвращаем базовую структуру
        vk_docs = {
            "version": "5.199",
            "last_updated": datetime.now().isoformat(),
            "methods": {
                "messages": {
                    "send": {
                        "description": "Отправка сообщения",
                        "parameters": ["peer_id", "message", "random_id"],
                        "example": "vk.messages.send(peer_id=2000000001, message='Привет!', random_id=get_random_id())"
                    },
                    "getConversations": {
                        "description": "Получение списка бесед",
                        "parameters": ["count", "offset"],
                        "example": "vk.messages.getConversations(count=20)"
                    }
                },
                "users": {
                    "get": {
                        "description": "Получение информации о пользователях",
                        "parameters": ["user_ids", "fields"],
                        "example": "vk.users.get(user_ids=[1, 2, 3])"
                    }
                },
                "groups": {
                    "getById": {
                        "description": "Получение информации о группах",
                        "parameters": ["group_id", "fields"],
                        "example": "vk.groups.getById(group_id=1)"
                    }
                }
            },
            "rate_limits": {
                "requests_per_second": 3,
                "requests_per_day": 10000
            },
            "best_practices": [
                "Используйте Long Poll для получения сообщений",
                "Применяйте rate limiting (3 сек между сообщениями)",
                "Работайте только с беседами (peer_id > 2000000000)",
                "Всегда проверяйте валидность токенов"
            ]
        }
        
        return vk_docs
    
    def refresh_python_libs_docs(self) -> Dict:
        """Обновление документации Python библиотек"""
        logger.info("🔄 Обновление документации Python библиотек...")
        
        python_docs = {
            "last_updated": datetime.now().isoformat(),
            "libraries": {
                "vk-api": {
                    "version": "11.10.0",
                    "description": "Python библиотека для работы с VK API",
                    "installation": "pip install vk-api==11.10.0",
                    "basic_usage": """
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

# Инициализация
vk_session = vk_api.VkApi(token='your_token')
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

# Обработка сообщений
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            vk.messages.send(
                user_id=event.user_id,
                message='Привет!',
                random_id=get_random_id()
            )
                    """,
                    "async_usage": """
import asyncio
import aiohttp

async def send_message_async(peer_id, message):
    async with aiohttp.ClientSession() as session:
        url = "https://api.vk.com/method/messages.send"
        params = {
            'peer_id': peer_id,
            'message': message,
            'access_token': token,
            'v': '5.199'
        }
        async with session.post(url, params=params) as response:
            return await response.json()
                    """
                },
                "aiohttp": {
                    "version": "3.12.15",
                    "description": "Асинхронная HTTP библиотека",
                    "installation": "pip install aiohttp==3.12.15"
                },
                "python-dotenv": {
                    "version": "1.1.1",
                    "description": "Загрузка переменных окружения из .env файлов",
                    "installation": "pip install python-dotenv==1.1.1"
                }
            }
        }
        
        return python_docs
    
    def refresh_all_docs(self) -> Dict:
        """Обновление всей документации"""
        logger.info("🚀 Начинаем обновление документации...")
        
        if not self.check_context7_availability():
            logger.warning("Context7 недоступен, используем локальную документацию")
        
        # Обновляем документацию
        docs = {
            "last_refresh": datetime.now().isoformat(),
            "vk_api": self.refresh_vk_api_docs(),
            "python_libs": self.refresh_python_libs_docs(),
            "context7_status": self.check_context7_availability()
        }
        
        # Сохраняем в кэш
        self.save_cache(docs)
        
        logger.info("✅ Документация обновлена")
        return docs
    
    def get_docs_summary(self) -> str:
        """Получение сводки документации"""
        cache = self.load_cache()
        
        if not cache:
            return "Документация не найдена. Запустите 'refresh docs' для обновления."
        
        summary = f"""
📚 СВОДКА ДОКУМЕНТАЦИИ
{'='*50}
🕒 Последнее обновление: {cache.get('last_refresh', 'Неизвестно')}
🔧 Context7 статус: {'✅ Доступен' if cache.get('context7_status') else '❌ Недоступен'}

📖 VK API:
  • Версия: {cache.get('vk_api', {}).get('version', 'Неизвестно')}
  • Методы: {len(cache.get('vk_api', {}).get('methods', {}))}
  • Rate limit: {cache.get('vk_api', {}).get('rate_limits', {}).get('requests_per_second', 'Неизвестно')} req/sec

🐍 Python библиотеки:
  • vk-api: {cache.get('python_libs', {}).get('libraries', {}).get('vk-api', {}).get('version', 'Неизвестно')}
  • aiohttp: {cache.get('python_libs', {}).get('libraries', {}).get('aiohttp', {}).get('version', 'Неизвестно')}
  • python-dotenv: {cache.get('python_libs', {}).get('libraries', {}).get('python-dotenv', {}).get('version', 'Неизвестно')}
        """
        
        return summary.strip()

def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование: python refresh_docs.py [refresh|status|check]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    manager = Context7Manager()
    
    if command == "refresh":
        docs = manager.refresh_all_docs()
        print("✅ Документация обновлена")
        print(f"📅 Время обновления: {docs['last_refresh']}")
        
    elif command == "status":
        print(manager.get_docs_summary())
        
    elif command == "check":
        if manager.check_context7_availability():
            print("✅ Context7 доступен")
        else:
            print("❌ Context7 недоступен")
            
    else:
        print("Неизвестная команда. Используйте: refresh, status, check")

if __name__ == "__main__":
    main()

