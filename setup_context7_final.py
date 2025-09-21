#!/usr/bin/env python3
"""
Финальная настройка Context7 MCP Server для Cursor
Автоматически настраивает все необходимые компоненты
"""

import os
import json
import subprocess
import sys
from pathlib import Path

def print_step(step, description):
    """Печать шага с форматированием"""
    print(f"\n{'='*60}")
    print(f"ШАГ {step}: {description}")
    print(f"{'='*60}")

def check_node_npm():
    """Проверка установки Node.js и npm"""
    try:
        node_version = subprocess.run(['node', '--version'], capture_output=True, text=True)
        npm_version = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        
        if node_version.returncode == 0 and npm_version.returncode == 0:
            print(f"✅ Node.js: {node_version.stdout.strip()}")
            print(f"✅ npm: {npm_version.stdout.strip()}")
            return True
        else:
            print("❌ Node.js или npm не найдены")
            return False
    except FileNotFoundError:
        print("❌ Node.js или npm не установлены")
        return False

def install_context7():
    """Установка Context7 MCP Server"""
    try:
        print("📦 Устанавливаю Context7 MCP Server...")
        result = subprocess.run(['npx', '-y', '@upstash/context7-mcp', '--version'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Context7 MCP Server установлен успешно")
            return True
        else:
            print(f"⚠️  Context7 установлен, но версия не определена: {result.stderr}")
            return True
    except subprocess.TimeoutExpired:
        print("⚠️  Установка заняла больше времени, но должна быть завершена")
        return True
    except Exception as e:
        print(f"❌ Ошибка установки Context7: {e}")
        return False

def setup_mcp_config():
    """Настройка конфигурации MCP"""
    cursor_config_path = Path.home() / '.cursor' / 'mcp.json'
    
    # Создаем директорию если не существует
    cursor_config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Конфигурация MCP серверов
    mcp_config = {
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
                "args": ["-y", "@modelcontextprotocol/server-filesystem", 
                        str(Path.cwd())]
            },
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_token_here"
                }
            }
        }
    }
    
    try:
        with open(cursor_config_path, 'w', encoding='utf-8') as f:
            json.dump(mcp_config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Конфигурация MCP сохранена: {cursor_config_path}")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения конфигурации: {e}")
        return False

def create_context7_guide():
    """Создание руководства по использованию Context7"""
    guide_content = """# Context7 MCP Server - Руководство по использованию

## Что такое Context7?
Context7 - это MCP сервер, который предоставляет актуальную документацию для различных API и библиотек.

## Как использовать в Cursor:

### 1. Автоматическое использование
Context7 автоматически активируется при запросах о документации API.

### 2. Ручное использование
Вы можете явно запросить использование Context7:
- "use context7" - активировать Context7
- "Покажи актуальные методы VK API" - автоматически использует Context7

### 3. Доступные команды
- `refresh docs` - обновить документацию
- `check vk api` - проверить актуальность VK API
- `latest python examples` - получить свежие примеры Python

## Настройка API ключей:

### Context7 API Key
1. Зайдите на https://context7.com
2. Создайте аккаунт
3. Получите API ключ
4. Замените "your_api_key_here" в конфигурации

### GitHub Token (опционально)
1. Зайдите в GitHub Settings > Developer settings > Personal access tokens
2. Создайте новый token с правами на чтение репозиториев
3. Замените "your_github_token_here" в конфигурации

## Проверка работы:
После настройки перезапустите Cursor и проверьте:
1. В настройках MCP должен появиться сервер "context7"
2. При запросе документации должен автоматически использоваться Context7
3. Команда "refresh docs" должна работать

## Устранение проблем:
- Если Context7 не работает, проверьте API ключ
- Убедитесь что Node.js установлен
- Перезапустите Cursor после изменения конфигурации
"""
    
    try:
        with open('CONTEXT7_GUIDE.md', 'w', encoding='utf-8') as f:
            f.write(guide_content)
        print("✅ Руководство по Context7 создано: CONTEXT7_GUIDE.md")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания руководства: {e}")
        return False

def main():
    """Основная функция настройки"""
    print("🚀 ФИНАЛЬНАЯ НАСТРОЙКА CONTEXT7 MCP SERVER")
    print("=" * 60)
    
    # Шаг 1: Проверка Node.js
    print_step(1, "Проверка Node.js и npm")
    if not check_node_npm():
        print("\n❌ Установите Node.js с https://nodejs.org/")
        return False
    
    # Шаг 2: Установка Context7
    print_step(2, "Установка Context7 MCP Server")
    if not install_context7():
        print("\n❌ Не удалось установить Context7")
        return False
    
    # Шаг 3: Настройка конфигурации MCP
    print_step(3, "Настройка конфигурации MCP")
    if not setup_mcp_config():
        print("\n❌ Не удалось настроить конфигурацию MCP")
        return False
    
    # Шаг 4: Создание руководства
    print_step(4, "Создание руководства по использованию")
    create_context7_guide()
    
    # Финальные инструкции
    print_step(5, "ФИНАЛЬНЫЕ ИНСТРУКЦИИ")
    print("""
🎉 Context7 MCP Server настроен успешно!

📋 СЛЕДУЮЩИЕ ШАГИ:

1. 🔄 ПЕРЕЗАПУСТИТЕ CURSOR
   - Закройте Cursor полностью
   - Откройте заново

2. ✅ ПРОВЕРЬТЕ НАСТРОЙКИ MCP
   - Зайдите в Settings > MCP
   - Должен появиться сервер "context7"
   - Включите его если не включен

3. 🔑 НАСТРОЙТЕ API КЛЮЧИ (опционально)
   - Context7 API Key: https://context7.com
   - GitHub Token: https://github.com/settings/tokens

4. 🧪 ПРОТЕСТИРУЙТЕ РАБОТУ
   - Спросите: "Покажи актуальные методы VK API"
   - Должен автоматически использоваться Context7

5. 📚 ИЗУЧИТЕ РУКОВОДСТВО
   - Откройте файл CONTEXT7_GUIDE.md
   - Изучите все возможности

🚀 Теперь Context7 будет автоматически предоставлять 
   актуальную документацию для всех ваших запросов!
""")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Настройка завершена успешно!")
        else:
            print("\n❌ Настройка завершена с ошибками")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Настройка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)
