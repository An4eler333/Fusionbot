#!/usr/bin/env python3
"""
Тест получения реальных сообщений
"""
import os
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from dotenv import load_dotenv
import time

# Загружаем переменные окружения
load_dotenv('ТОКЕНЫ.env')

def test_real_messages():
    """Тестирование получения реальных сообщений"""
    vk_token = os.getenv('VK_TOKEN')
    group_id = os.getenv('VK_GROUP_ID')
    
    print(f"🔍 Тестирование получения реальных сообщений...")
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
        print("💡 Напишите 'тест' в любую беседу где добавлен бот")
        
        message_count = 0
        
        # Слушаем сообщения
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                message_count += 1
                print(f"\n📨 Сообщение #{message_count}:")
                print(f"   От: {event.user_id}")
                print(f"   В чат: {event.peer_id}")
                print(f"   Текст: '{event.text}'")
                print(f"   Время: {event.datetime}")
                print(f"   Тип чата: {'Беседа' if event.peer_id > 2000000000 else 'Личка'}")
                
                # Проверяем, что это беседа
                if event.peer_id <= 2000000000:
                    print("⚠️  Это личное сообщение, бот работает только в беседах")
                    continue
                
                # Отвечаем на сообщение
                if event.text.lower() in ['тест', 'test']:
                    try:
                        vk.messages.send(
                            peer_id=event.peer_id,
                            message="✅ Тест получен! Бот работает!",
                            random_id=vk_api.utils.get_random_id()
                        )
                        print("✅ Ответ отправлен")
                    except Exception as e:
                        print(f"❌ Ошибка отправки ответа: {e}")
                elif event.text.lower() in ['помощь', 'help']:
                    try:
                        help_text = """🤖 VK Бот Fusionbot v6.0

📋 Доступные команды:
• помощь - эта справка
• тест - тестовое сообщение
• ии [вопрос] - поговорить с ИИ
• шутка - получить шутку
• история - короткая история
• комплимент - получить комплимент
• топ - топ участников чата
• ранг - узнать свой ранг
• статистика - статистика бота

🎯 Система рангов: от Новичка до Космоса!
💬 Работаем только в беседах"""
                        vk.messages.send(
                            peer_id=event.peer_id,
                            message=help_text,
                            random_id=vk_api.utils.get_random_id()
                        )
                        print("✅ Справка отправлена")
                    except Exception as e:
                        print(f"❌ Ошибка отправки справки: {e}")
                else:
                    print("💬 Сообщение получено, но не команда")
                
                print("---")
        
    except KeyboardInterrupt:
        print(f"\n🛑 Тест остановлен пользователем. Получено сообщений: {message_count}")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    test_real_messages()
