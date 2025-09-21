#!/usr/bin/env python3
"""
Проверка ID группы по ссылке
"""
import os
import vk_api
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('ТОКЕНЫ.env')

def check_group_id():
    """Проверка ID группы"""
    vk_token = os.getenv('VK_TOKEN')
    
    print(f"🔍 Проверка ID группы...")
    print(f"📋 Токен: {vk_token[:20]}...")
    
    if not vk_token:
        print("❌ Токен не установлен")
        return False
    
    try:
        # Инициализация VK API
        vk_session = vk_api.VkApi(token=vk_token)
        vk = vk_session.get_api()
        
        print("✅ VK API инициализирован")
        
        # Проверяем группу по screen_name
        screen_name = "cfusion180925"  # из ссылки vk.com/cfusion180925
        
        try:
            # Получаем информацию о группе по screen_name
            group_info = vk.groups.getById(group_id=screen_name)
            if group_info and len(group_info) > 0:
                group = group_info[0]
                print(f"🏢 Группа найдена:")
                print(f"   ID: {group['id']}")
                print(f"   Имя: {group['name']}")
                print(f"   Screen name: {group.get('screen_name', 'N/A')}")
                print(f"   Тип: {group.get('type', 'N/A')}")
                
                # Проверяем текущий ID в файле
                current_id = os.getenv('VK_GROUP_ID')
                print(f"\n📋 Текущий ID в файле: {current_id}")
                print(f"📋 Правильный ID: {group['id']}")
                
                if str(current_id) != str(group['id']):
                    print("❌ ID группы не совпадает!")
                    print(f"💡 Нужно обновить VK_GROUP_ID на: {group['id']}")
                    return group['id']
                else:
                    print("✅ ID группы правильный")
                    return True
            else:
                print("❌ Группа не найдена")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка получения информации о группе: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False

if __name__ == "__main__":
    result = check_group_id()
    if isinstance(result, int):
        print(f"\n🔧 Нужно обновить VK_GROUP_ID на: {result}")
    elif result:
        print("\n✅ ID группы правильный")
    else:
        print("\n❌ Проблема с проверкой группы")
