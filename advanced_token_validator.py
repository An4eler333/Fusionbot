#!/usr/bin/env python3
"""
Продвинутый валидатор VK токенов
Показывает детальную информацию о проблемах с токеном
"""

import os
import vk_api
from dotenv import load_dotenv

def validate_vk_token_detailed():
    """Детальная валидация VK токена"""
    print("🔍 ПРОДВИНУТАЯ ПРОВЕРКА VK ТОКЕНА")
    print("=" * 60)
    
    # Загружаем токены
    load_dotenv('ТОКЕНЫ.env')
    token = os.getenv('VK_TOKEN')
    group_id = os.getenv('VK_GROUP_ID')
    
    if not token:
        print("❌ VK_TOKEN не найден в файле ТОКЕНЫ.env")
        return False
    
    if not group_id:
        print("❌ VK_GROUP_ID не найден в файле ТОКЕНЫ.env")
        return False
    
    print(f"📋 Токен: {token[:20]}...")
    print(f"📋 Group ID: {group_id}")
    
    # Проверяем формат токена
    if not token.startswith('vk1.a.'):
        print("❌ Неверный формат токена. Должен начинаться с 'vk1.a.'")
        return False
    
    print("✅ Формат токена корректный")
    
    try:
        # Создаем сессию
        session = vk_api.VkApi(token=token)
        vk = session.get_api()
        
        print("✅ Сессия VK API создана")
        
        # Тест 1: Получение информации о пользователе
        try:
            user_info = vk.users.get()
            if user_info and len(user_info) > 0:
                user = user_info[0]
                print(f"✅ Пользователь: {user.get('first_name', 'N/A')} {user.get('last_name', 'N/A')}")
                print(f"✅ User ID: {user.get('id', 'N/A')}")
            else:
                print("❌ Не удалось получить информацию о пользователе")
                return False
        except Exception as e:
            print(f"❌ Ошибка получения информации о пользователе: {e}")
            return False
        
        # Тест 2: Проверка прав токена
        try:
            # Проверяем права на сообщения
            try:
                conversations = vk.messages.getConversations(count=1)
                print("✅ Право на messages.getConversations: OK")
            except Exception as e:
                print(f"⚠️  Право на messages.getConversations: {e}")
            
            # Проверяем права на группы
            try:
                groups = vk.groups.getById(group_id=group_id)
                if groups and len(groups) > 0:
                    group = groups[0]
                    print(f"✅ Группа: {group.get('name', 'N/A')}")
                    print(f"✅ Group ID: {group.get('id', 'N/A')}")
                else:
                    print("❌ Группа не найдена или нет доступа")
            except Exception as e:
                print(f"❌ Ошибка получения информации о группе: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка проверки прав: {e}")
            return False
        
        # Тест 3: Проверка возможности отправки сообщений
        try:
            # Пробуем получить список бесед (это безопасно)
            conversations = vk.messages.getConversations(count=1)
            print("✅ Право на получение бесед: OK")
        except Exception as e:
            print(f"❌ Нет права на получение бесед: {e}")
            return False
        
        print("\n🎉 ТОКЕН ВАЛИДЕН И ГОТОВ К ИСПОЛЬЗОВАНИЮ!")
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False

def show_token_requirements():
    """Показывает требования к токену"""
    print("\n📋 ТРЕБОВАНИЯ К VK ТОКЕНУ:")
    print("=" * 60)
    print("1. Формат: vk1.a.xxxxxxxxxxxxxxxxxxxxxxxx")
    print("2. Права доступа:")
    print("   - messages (отправка и получение сообщений)")
    print("   - groups (работа с группами)")
    print("   - offline (долгосрочный доступ)")
    print("3. Тип токена: Community Token (токен сообщества)")
    print("4. Срок действия: не истек")
    
    print("\n🔧 КАК ПОЛУЧИТЬ ПРАВИЛЬНЫЙ ТОКЕН:")
    print("=" * 60)
    print("1. Зайдите в https://vk.com/groups?act=manage")
    print("2. Выберите вашу группу")
    print("3. Перейдите в 'Управление' → 'Работа с API'")
    print("4. Создайте токен с правами:")
    print("   ✅ messages")
    print("   ✅ groups") 
    print("   ✅ offline")
    print("5. Скопируйте токен и обновите ТОКЕНЫ.env")

def main():
    """Основная функция"""
    success = validate_vk_token_detailed()
    
    if not success:
        show_token_requirements()
        print("\n❌ Токен не прошел валидацию")
        return False
    else:
        print("\n✅ Токен готов к использованию!")
        print("🚀 Теперь можно запускать бота: python vk_bot.py")
        return True

if __name__ == "__main__":
    main()

