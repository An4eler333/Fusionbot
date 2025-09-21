# Настройка Context7 MCP Server в Cursor

## 🚀 БЫСТРАЯ НАСТРОЙКА

### 1. Установка Context7 (уже выполнено)
```bash
npm install -g @upstash/context7-mcp
```

### 2. Настройка Cursor

#### Вариант A: Через настройки Cursor
1. Откройте Cursor
2. Перейдите в Settings (Ctrl+,)
3. Найдите раздел "MCP Servers"
4. Добавьте новый сервер:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": {
        "CONTEXT7_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

#### Вариант B: Через конфигурационный файл
1. Создайте файл `~/.cursor/mcp_config.json` (Windows: `%APPDATA%\Cursor\mcp_config.json`)
2. Скопируйте содержимое из `cursor_mcp_config.json`

### 3. Перезапуск Cursor
После настройки перезапустите Cursor для применения изменений.

## 🔧 РАСШИРЕННАЯ НАСТРОЙКА

### Настройка для VK разработки
Используйте файл `context7_vk_config.json` для специализированной настройки:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": {
        "CONTEXT7_API_KEY": "your_api_key_here",
        "CONTEXT7_BASE_URL": "https://api.context7.com",
        "CONTEXT7_LIBRARIES": "vk-api,python-vk-api,vk-bot",
        "CONTEXT7_DOCS_SOURCES": "vk.com/dev,github.com/vk-api"
      }
    }
  }
}
```

### Автоматическое использование
Context7 будет автоматически использоваться при запросах содержащих:
- "vk api", "vk-api", "vk_api"
- "python vk", "python-vk"
- "vk bot", "vk-bot", "vk_bot"
- "актуальная документация", "latest documentation"

## 🧪 ТЕСТИРОВАНИЕ

### Проверка установки
```bash
# Проверка Context7
npx -y @upstash/context7-mcp --help

# Проверка статуса
python refresh_docs.py status

# Обновление документации
python refresh_docs.py refresh
```

### Тестовые запросы
После настройки попробуйте следующие запросы в Cursor:

1. **"Покажи актуальные методы VK API для отправки сообщений"**
2. **"Какая последняя версия python-vk-api библиотеки?"**
3. **"Как правильно использовать Long Poll в VK API?"**

Context7 должен автоматически предоставить актуальную документацию.

## 🔑 ПОЛУЧЕНИЕ API КЛЮЧА

### Бесплатный план Upstash
1. Перейдите на https://upstash.com/
2. Создайте бесплатный аккаунт
3. Создайте Redis базу данных
4. Получите API ключ в настройках

### Альтернатива: Локальная работа
Context7 может работать и без API ключа, используя локальную документацию.

## 📋 КОМАНДЫ УПРАВЛЕНИЯ

### Обновление документации
```bash
python refresh_docs.py refresh
```

### Проверка статуса
```bash
python refresh_docs.py status
```

### Проверка Context7
```bash
python refresh_docs.py check
```

### Автоматическое улучшение ответов
```bash
python auto_context7.py setup
```

## 🛠️ УСТРАНЕНИЕ НЕПОЛАДОК

### Context7 не отвечает
1. Проверьте установку: `npx -y @upstash/context7-mcp --help`
2. Проверьте API ключ в конфигурации
3. Перезапустите Cursor

### Документация не обновляется
1. Запустите: `python refresh_docs.py refresh`
2. Проверьте кэш: `python refresh_docs.py status`
3. Убедитесь в наличии интернет-соединения

### Cursor не видит MCP сервер
1. Проверьте путь к конфигурационному файлу
2. Убедитесь в правильности JSON синтаксиса
3. Перезапустите Cursor

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

- [Официальная документация Context7](https://context7.com)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Cursor MCP Integration](https://docs.cursor.com/guides/mcp)
- [VK API Documentation](https://vk.com/dev)

## ✅ ПРОВЕРКА РАБОТЫ

После настройки Context7 должен:
1. ✅ Автоматически использоваться при запросах о VK API
2. ✅ Предоставлять актуальную документацию
3. ✅ Обновлять версии библиотек
4. ✅ Показывать свежие примеры кода

Если все работает правильно, вы увидите в ответах AI пометку о том, что документация получена через Context7.

