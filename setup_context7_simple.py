#!/usr/bin/env python3
"""
Упрощенная настройка Context7 MCP Server
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_cursor_config():
    """Создание конфигурации Cursor"""
    logger.info("⚙️ Создание конфигурации Cursor...")
    
    # Определяем путь к конфигурации Cursor
    if os.name == 'nt':  # Windows
        config_dir = Path(os.environ.get('APPDATA', '')) / 'Cursor'
    else:  # Linux/Mac
        config_dir = Path.home() / '.config' / 'cursor'
    
    # Создаем директорию
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Создаем конфигурационный файл
    config_file = config_dir / 'mcp_config.json'
    
    config = {
        "mcpServers": {
            "context7": {
                "command": "npx",
                "args": ["-y", "@upstash/context7-mcp"],
                "env": {
                    "CONTEXT7_API_KEY": "your_api_key_here",
                    "CONTEXT7_BASE_URL": "https://api.context7.com"
                }
            }
        }
    }
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Конфигурация Cursor создана: {config_file}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка создания конфигурации: {e}")
        return False

def create_project_configs():
    """Создание конфигураций проекта"""
    logger.info("📁 Создание конфигураций проекта...")
    
    # Создаем директорию для конфигураций
    context7_dir = Path('context7_config')
    context7_dir.mkdir(exist_ok=True)
    
    # Создаем README
    readme_content = f"""# Context7 Configuration

## Настройка Context7 MCP Server для VK Bot проекта

### Файлы конфигурации:
- `cursor_mcp_config.json` - Основная конфигурация для Cursor
- `context7_vk_config.json` - Специализированная конфигурация для VK API
- `auto_context7_config.json` - Автоматическое использование

### Установка:
1. Скопируйте содержимое `cursor_mcp_config.json` в настройки Cursor
2. Перезапустите Cursor
3. Context7 будет автоматически использоваться для VK API запросов

### Команды:
```bash
# Обновление документации
python refresh_docs.py refresh

# Проверка статуса
python refresh_docs.py status

# Настройка автоиспользования
python auto_context7.py setup
```

### Автоматическое использование:
Context7 будет автоматически использоваться при запросах содержащих:
- "vk api", "vk-api", "vk_api"
- "python vk", "python-vk"
- "актуальная документация"
- "latest documentation"

Создано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    try:
        with open(context7_dir / 'README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info("✅ Конфигурации проекта созданы")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка создания конфигураций: {e}")
        return False

def main():
    """Главная функция"""
    print("🚀 Упрощенная настройка Context7 MCP Server")
    print("=" * 50)
    
    success = True
    
    # Создаем конфигурацию Cursor
    if not create_cursor_config():
        success = False
    
    # Создаем конфигурации проекта
    if not create_project_configs():
        success = False
    
    if success:
        print("""
🎉 НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!

📋 СЛЕДУЮЩИЕ ШАГИ:
1. Перезапустите Cursor
2. Context7 будет автоматически использоваться для VK API запросов
3. Попробуйте запрос: "Покажи актуальные методы VK API"

🔧 КОМАНДЫ УПРАВЛЕНИЯ:
• python refresh_docs.py refresh    - Обновить документацию
• python refresh_docs.py status     - Статус документации
• python auto_context7.py setup     - Настроить автоиспользование

📚 ДОКУМЕНТАЦИЯ:
• CURSOR_CONTEXT7_SETUP.md - Подробные инструкции
• context7_config/ - Конфигурационные файлы

💡 Теперь каждый запрос о VK API будет автоматически
   получать актуальную документацию через Context7!
        """)
    else:
        print("""
❌ НАСТРОЙКА ЗАВЕРШЕНА С ОШИБКАМИ

📋 Проверьте логи выше для деталей
        """)

if __name__ == "__main__":
    main()

