#!/usr/bin/env python3
"""
Тест получения сообщений от VK API
"""
import os
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('ТОКЕНЫ.env')

def test_messages():
    """Тестирование получения сообщений"""
    vk_token = os.getenv('VK_TOKEN')
    group_id = os.getenv('VK_GROUP_ID')
    
    print(f"🔍 Тестирование получения сообщений...")
    print(f"📋 Токен: {vk_token[:20]}...")
    print(f"🏢 ID группы: {group_id}")
    
    if not vk_token or not group_id:
        print("❌ Токен или ID группы не установлены")
        return False
    
    try:
        # Инициализация VK API
        vk_session = vk_api.VkApi(token=vk_token)
        vk = vk_session.get_api()
        longpoll = VkLongPoll(vk_session)
        
        print("✅ VK API инициализирован")
        print("🔍 Ожидание сообщений... (нажмите Ctrl+C для остановки)")
        
        # Слушаем сообщения
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                print(f"📨 Получено сообщение:")
                print(f"   От: {event.user_id}")
                print(f"   В чат: {event.peer_id}")
                print(f"   Текст: {event.text}")
                print(f"   Время: {event.datetime}")
                print("---")
                
                # Отвечаем на сообщение
                if event.text.lower() in ['тест', 'test']:
                    vk.messages.send(
                        peer_id=event.peer_id,
                        message="✅ Тест получен! Бот работает!",
                        random_id=vk_api.utils.get_random_id()
                    )
                    print("✅ Ответ отправлен")
        
    except KeyboardInterrupt:
        print("\n🛑 Тест остановлен пользователем")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    test_messages()
