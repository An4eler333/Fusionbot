#!/usr/bin/env python3
"""
Главный скрипт запуска VK Bot Fusionbot v6.0
"""
import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from async_vk_bot import AsyncVKBot, BotConfig
from monitoring import monitoring_service
from error_handler import error_handler, data_validator

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

def print_banner():
    """Вывод баннера"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🤖 VK BOT FUSIONBOT v6.0                 ║
║                                                              ║
║  ✨ Продвинутый VK бот с ИИ и системой рангов               ║
║  🧠 ИИ система: Groq API + локальные ответы                 ║
║  🏆 Система рангов: 10 уровней от Новичка до Космоса        ║
║  🛡️ Безопасность: защита от флуда, валидация данных        ║
║  📊 Мониторинг: метрики, логирование, дашборд               ║
║  🔄 Async архитектура: современный Python                   ║
║                                                              ║
║  🚀 Запуск: {timestamp}                                      ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

def check_requirements():
    """Проверка требований"""
    logger.info("🔍 Проверка требований...")
    
    # Проверяем Python версию
    if sys.version_info < (3, 11):
        logger.error("❌ Требуется Python 3.11 или выше")
        return False
    
    # Проверяем наличие файла с токенами
    if not os.path.exists('ТОКЕНЫ.env'):
        logger.error("❌ Файл ТОКЕНЫ.env не найден")
        return False
    
    # Загружаем переменные окружения
    load_dotenv('ТОКЕНЫ.env')
    
    # Проверяем токены
    vk_token = os.getenv('VK_TOKEN')
    group_id = os.getenv('VK_GROUP_ID')
    
    if not vk_token or not group_id:
        logger.warning("⚠️  Токены не установлены, будет использован демо-режим")
    
    logger.info("✅ Требования проверены")
    return True

def validate_tokens():
    """Валидация токенов"""
    logger.info("🔐 Валидация токенов...")
    
    try:
        from token_validator import check_current_tokens
        return check_current_tokens()
    except Exception as e:
        logger.error(f"❌ Ошибка валидации токенов: {e}")
        return False

async def run_bot_with_monitoring():
    """Запуск бота с мониторингом"""
    logger.info("🚀 Запуск бота с системой мониторинга...")
    
    # Создаем конфигурацию
    config = BotConfig(
        vk_token=os.getenv('VK_TOKEN', ''),
        group_id=int(os.getenv('VK_GROUP_ID', 0)),
        groq_api_key=os.getenv('GROQ_API_KEY', ''),
        demo_mode=not os.getenv('VK_TOKEN') or not os.getenv('VK_GROUP_ID')
    )
    
    # Создаем бота
    bot = AsyncVKBot(config)
    
    # Запускаем мониторинг в фоне
    monitoring_task = asyncio.create_task(monitoring_service.start_monitoring(interval=60))
    
    try:
        # Инициализируем и запускаем бота
        if await bot.initialize():
            logger.info("✅ Бот инициализирован успешно")
            await bot.run()
        else:
            logger.error("❌ Не удалось инициализировать бота")
            return False
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        error_handler.handle_error(
            e, 
            category=error_handler.ErrorCategory.UNKNOWN,
            severity=error_handler.ErrorSeverity.CRITICAL
        )
        return False
    finally:
        # Останавливаем мониторинг
        monitoring_service.stop_monitoring()
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass
        
        logger.info("🛑 Бот остановлен")
    
    return True

async def run_demo_mode():
    """Запуск в демо-режиме"""
    logger.info("🎭 Запуск в демо-режиме...")
    
    config = BotConfig(
        vk_token='',
        group_id=0,
        groq_api_key='',
        demo_mode=True
    )
    
    bot = AsyncVKBot(config)
    
    try:
        if await bot.initialize():
            await bot.run()
        else:
            logger.error("❌ Не удалось инициализировать демо-режим")
            return False
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Ошибка в демо-режиме: {e}")
        return False
    
    return True

def run_tests():
    """Запуск тестов"""
    logger.info("🧪 Запуск тестов...")
    
    try:
        import pytest
        result = pytest.main(['tests/', '-v', '--tb=short'])
        return result == 0
    except ImportError:
        logger.error("❌ pytest не установлен. Установите: pip install pytest")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка запуска тестов: {e}")
        return False

def show_status():
    """Показать статус системы"""
    logger.info("📊 Статус системы...")
    
    try:
        from monitoring import monitoring_service
        monitoring_service.dashboard.print_dashboard()
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса: {e}")
        return False

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='VK Bot Fusionbot v6.0')
    parser.add_argument('--mode', choices=['normal', 'demo', 'test', 'status'], 
                       default='normal', help='Режим запуска')
    parser.add_argument('--validate-tokens', action='store_true', 
                       help='Валидировать токены и выйти')
    parser.add_argument('--no-banner', action='store_true', 
                       help='Не показывать баннер')
    
    args = parser.parse_args()
    
    # Показываем баннер
    if not args.no_banner:
        print_banner()
    
    # Проверяем требования
    if not check_requirements():
        sys.exit(1)
    
    # Валидация токенов
    if args.validate_tokens:
        if validate_tokens():
            logger.info("✅ Токены валидны")
            sys.exit(0)
        else:
            logger.error("❌ Токены невалидны")
            sys.exit(1)
    
    # Выбираем режим
    if args.mode == 'demo':
        success = asyncio.run(run_demo_mode())
    elif args.mode == 'test':
        success = run_tests()
    elif args.mode == 'status':
        success = show_status()
    else:  # normal
        if validate_tokens():
            success = asyncio.run(run_bot_with_monitoring())
        else:
            logger.warning("⚠️  Токены невалидны, запуск в демо-режиме")
            success = asyncio.run(run_demo_mode())
    
    if success:
        logger.info("✅ Выполнение завершено успешно")
        sys.exit(0)
    else:
        logger.error("❌ Выполнение завершено с ошибками")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        input("\n👆 Нажми Enter для выхода...")

