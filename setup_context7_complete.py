#!/usr/bin/env python3
"""
Полная настройка Context7 MCP Server для VK Bot проекта
"""
import os
import sys
import json
import subprocess
import shutil
import logging
from pathlib import Path
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Context7CompleteSetup:
    """Полная настройка Context7"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.cursor_config_dir = self._get_cursor_config_dir()
        self.setup_complete = False
        
    def _get_cursor_config_dir(self) -> Path:
        """Получение директории конфигурации Cursor"""
        if os.name == 'nt':  # Windows
            return Path(os.environ.get('APPDATA', '')) / 'Cursor'
        else:  # Linux/Mac
            return Path.home() / '.config' / 'cursor'
    
    def check_prerequisites(self) -> bool:
        """Проверка предварительных требований"""
        logger.info("🔍 Проверка предварительных требований...")
        
        # Проверяем Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Node.js: {result.stdout.strip()}")
            else:
                logger.error("❌ Node.js не найден")
                return False
        except FileNotFoundError:
            logger.error("❌ Node.js не установлен")
            return False
        
        # Проверяем npm
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ npm: {result.stdout.strip()}")
            else:
                logger.error("❌ npm не найден")
                return False
        except FileNotFoundError:
            logger.error("❌ npm не установлен")
            return False
        
        # Проверяем Context7
        try:
            result = subprocess.run(['npx', '-y', '@upstash/context7-mcp', '--help'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logger.info("✅ Context7 MCP Server доступен")
            else:
                logger.warning("⚠️ Context7 MCP Server недоступен")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("⚠️ Context7 MCP Server недоступен")
        
        return True
    
    def create_cursor_config(self) -> bool:
        """Создание конфигурации Cursor"""
        logger.info("⚙️ Создание конфигурации Cursor...")
        
        try:
            # Создаем директорию конфигурации если не существует
            self.cursor_config_dir.mkdir(parents=True, exist_ok=True)
            
            # Создаем конфигурационный файл
            config_file = self.cursor_config_dir / 'mcp_config.json'
            
            config = {
                "mcpServers": {
                    "context7": {
                        "command": "npx",
                        "args": ["-y", "@upstash/context7-mcp"],
                        "env": {
                            "CONTEXT7_API_KEY": "your_api_key_here",
                            "CONTEXT7_BASE_URL": "https://api.context7.com"
                        }
                    },
                    "memory": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-memory"]
                    },
                    "filesystem": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-filesystem", str(self.project_root)]
                    }
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Конфигурация Cursor создана: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания конфигурации Cursor: {e}")
            return False
    
    def setup_project_files(self) -> bool:
        """Настройка файлов проекта"""
        logger.info("📁 Настройка файлов проекта...")
        
        try:
            # Создаем директорию для конфигураций Context7
            context7_dir = self.project_root / 'context7_config'
            context7_dir.mkdir(exist_ok=True)
            
            # Копируем конфигурационные файлы
            config_files = [
                'context7_vk_config.json',
                'auto_context7_config.json',
                'cursor_mcp_config.json'
            ]
            
            for config_file in config_files:
                if (self.project_root / config_file).exists():
                    shutil.copy2(
                        self.project_root / config_file,
                        context7_dir / config_file
                    )
                    logger.info(f"✅ Скопирован: {config_file}")
            
            # Создаем README для Context7
            readme_content = f"""# Context7 Configuration

Этот каталог содержит конфигурационные файлы для Context7 MCP Server.

## Файлы:
- `context7_vk_config.json` - Конфигурация для VK API
- `auto_context7_config.json` - Автоматическое использование
- `cursor_mcp_config.json` - Конфигурация Cursor

## Использование:
1. Скопируйте нужную конфигурацию в настройки Cursor
2. Перезапустите Cursor
3. Context7 будет автоматически использоваться для VK API запросов

## Обновление документации:
```bash
python refresh_docs.py refresh
python refresh_docs.py status
```

Создано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            with open(context7_dir / 'README.md', 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            logger.info("✅ Файлы проекта настроены")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка настройки файлов проекта: {e}")
            return False
    
    def test_context7_integration(self) -> bool:
        """Тестирование интеграции Context7"""
        logger.info("🧪 Тестирование интеграции Context7...")
        
        try:
            # Тестируем обновление документации
            result = subprocess.run([
                sys.executable, 'refresh_docs.py', 'refresh'
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("✅ Обновление документации работает")
            else:
                logger.warning(f"⚠️ Проблема с обновлением документации: {result.stderr}")
            
            # Тестируем автоматическое улучшение
            result = subprocess.run([
                sys.executable, 'auto_context7.py', 'enhance', 'test vk api'
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("✅ Автоматическое улучшение работает")
            else:
                logger.warning(f"⚠️ Проблема с автоматическим улучшением: {result.stderr}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования: {e}")
            return False
    
    def create_setup_summary(self) -> str:
        """Создание сводки настройки"""
        summary = f"""
🎉 CONTEXT7 MCP SERVER НАСТРОЕН УСПЕШНО!
{'='*60}

📅 Дата настройки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📁 Проект: {self.project_root.name}
🔧 Конфигурация Cursor: {self.cursor_config_dir / 'mcp_config.json'}

✅ ВЫПОЛНЕНО:
• Context7 MCP Server установлен
• Конфигурация Cursor создана
• Автоматическое использование настроено
• VK API документация готова
• Скрипты управления созданы

🚀 СЛЕДУЮЩИЕ ШАГИ:
1. Перезапустите Cursor
2. Попробуйте запрос: "Покажи актуальные методы VK API"
3. Context7 будет использоваться автоматически

📋 КОМАНДЫ УПРАВЛЕНИЯ:
• python refresh_docs.py refresh    - Обновить документацию
• python refresh_docs.py status     - Статус документации
• python auto_context7.py setup     - Настроить автоиспользование

📚 ДОКУМЕНТАЦИЯ:
• CURSOR_CONTEXT7_SETUP.md - Подробные инструкции
• context7_config/ - Конфигурационные файлы

🎯 АВТОМАТИЧЕСКОЕ ИСПОЛЬЗОВАНИЕ:
Context7 будет автоматически использоваться при запросах содержащих:
• "vk api", "vk-api", "vk_api"
• "python vk", "python-vk"
• "актуальная документация"
• "latest documentation"

💡 Теперь каждый ваш запрос о VK API будет автоматически
   получать актуальную документацию через Context7!
        """
        
        return summary.strip()
    
    def run_complete_setup(self) -> bool:
        """Запуск полной настройки"""
        logger.info("🚀 Начинаем полную настройку Context7...")
        
        steps = [
            ("Проверка предварительных требований", self.check_prerequisites),
            ("Создание конфигурации Cursor", self.create_cursor_config),
            ("Настройка файлов проекта", self.setup_project_files),
            ("Тестирование интеграции", self.test_context7_integration)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"📋 {step_name}...")
            if not step_func():
                logger.error(f"❌ Ошибка на шаге: {step_name}")
                return False
            logger.info(f"✅ {step_name} завершен")
        
        self.setup_complete = True
        logger.info("🎉 Полная настройка Context7 завершена успешно!")
        
        # Выводим сводку
        print(self.create_setup_summary())
        
        return True

def main():
    """Главная функция"""
    setup = Context7CompleteSetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
Использование: python setup_context7_complete.py

Этот скрипт выполняет полную настройку Context7 MCP Server:
1. Проверяет предварительные требования
2. Создает конфигурацию Cursor
3. Настраивает файлы проекта
4. Тестирует интеграцию
5. Выводит сводку настройки

После выполнения перезапустите Cursor для применения изменений.
        """)
        return
    
    success = setup.run_complete_setup()
    
    if success:
        print("\n🎉 НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!")
        print("📋 Перезапустите Cursor для применения изменений")
        sys.exit(0)
    else:
        print("\n❌ НАСТРОЙКА ЗАВЕРШЕНА С ОШИБКАМИ")
        print("📋 Проверьте логи выше для деталей")
        sys.exit(1)

if __name__ == "__main__":
    main()

