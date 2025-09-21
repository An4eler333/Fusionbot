# Context7 Configuration

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

Создано: 2025-09-21 19:36:47
