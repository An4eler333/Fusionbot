"""
Консольная панель администратора для VK Бота
"""
import os
import threading
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ConsoleAdmin:
    """Консольная панель управления ботом"""
    
    def __init__(self):
        self.bot = None
        self.stats = {
            'start_time': datetime.now(),
            'messages_processed': 0,
            'commands_executed': 0,
            'errors_count': 0
        }
        logger.info("🎛️ Консольная панель администратора инициализирована")
    
    def update_stats(self, stat_name: str, increment: int = 1):
        """Обновить статистику"""
        if stat_name in self.stats:
            self.stats[stat_name] += increment
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику"""
        uptime = datetime.now() - self.stats['start_time']
        return {
            **self.stats,
            'uptime': str(uptime).split('.')[0],  # Убираем микросекунды
            'status': 'running' if self.bot else 'stopped'
        }
    
    def print_status(self):
        """Вывести статус в консоль"""
        stats = self.get_stats()
        print("\n" + "="*50)
        print("🤖 СТАТУС VK БОТА")
        print("="*50)
        print(f"⏱️  Время работы: {stats['uptime']}")
        print(f"📨 Сообщений обработано: {stats['messages_processed']}")
        print(f"⚡ Команд выполнено: {stats['commands_executed']}")
        print(f"❌ Ошибок: {stats['errors_count']}")
        print(f"🔄 Статус: {stats['status']}")
        print("="*50)

# Глобальный экземпляр консольной панели
console_admin = ConsoleAdmin()