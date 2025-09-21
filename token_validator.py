"""
Утилита для проверки и валидации VK токенов
"""
import os
import sys
import logging
from dotenv import load_dotenv
import vk_api

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_vk_token(token: str, group_id: int = None) -> dict:
    """
    Валидация VK токена
    
    Args:
        token: VK токен для проверки
        group_id: ID группы (опционально)
    
    Returns:
        dict: Результат валидации с подробной информацией
    """
    result = {
        'valid': False,
        'user_info': None,
        'group_info': None,
        'permissions': [],
        'errors': []
    }
    
    try:
        # Инициализация VK API
        vk_session = vk_api.VkApi(token=token)
        vk = vk_session.get_api()
        
        # Проверка 1: Информация о пользователе
        try:
            user_info = vk.users.get()
            result['user_info'] = user_info[0]
            logger.info(f"✅ Пользователь: {user_info[0]['first_name']} {user_info[0]['last_name']}")
        except Exception as e:
            result['errors'].append(f"Ошибка получения информации о пользователе: {e}")
            return result
        
        # Проверка 2: Информация о группе (если указана)
        if group_id:
            try:
                group_info = vk.groups.getById(group_id=group_id)
                result['group_info'] = group_info[0]
                logger.info(f"✅ Группа: {group_info[0]['name']}")
            except Exception as e:
                result['errors'].append(f"Ошибка получения информации о группе: {e}")
        
        # Проверка 3: Права на сообщения
        try:
            vk.messages.getConversations(count=1)
            result['permissions'].append('messages')
            logger.info("✅ Права на работу с сообщениями")
        except Exception as e:
            result['errors'].append(f"Нет прав на работу с сообщениями: {e}")
        
        # Проверка 4: Права на группы
        try:
            vk.groups.get()
            result['permissions'].append('groups')
            logger.info("✅ Права на работу с группами")
        except Exception as e:
            result['errors'].append(f"Нет прав на работу с группами: {e}")
        
        # Проверка 5: Long Poll
        try:
            longpoll = vk_api.longpoll.VkLongPoll(vk_session)
            result['permissions'].append('longpoll')
            logger.info("✅ Права на Long Poll")
        except Exception as e:
            result['errors'].append(f"Нет прав на Long Poll: {e}")
        
        result['valid'] = len(result['errors']) == 0
        
    except Exception as e:
        result['errors'].append(f"Критическая ошибка: {e}")
        logger.error(f"❌ Критическая ошибка валидации: {e}")
    
    return result

def check_current_tokens():
    """Проверка текущих токенов из файла ТОКЕНЫ.env"""
    logger.info("🔍 Проверка токенов из файла ТОКЕНЫ.env...")
    
    # Загружаем переменные окружения
    load_dotenv('ТОКЕНЫ.env')
    
    vk_token = os.getenv('VK_TOKEN')
    group_id = int(os.getenv('VK_GROUP_ID', 0))
    groq_key = os.getenv('GROQ_API_KEY')
    
    if not vk_token:
        logger.error("❌ VK_TOKEN не найден в файле ТОКЕНЫ.env")
        return False
    
    if not group_id:
        logger.error("❌ VK_GROUP_ID не найден в файле ТОКЕНЫ.env")
        return False
    
    logger.info(f"📋 Найденные токены:")
    logger.info(f"   VK_TOKEN: {vk_token[:20]}...")
    logger.info(f"   VK_GROUP_ID: {group_id}")
    logger.info(f"   GROQ_API_KEY: {'✅ Найден' if groq_key else '❌ Не найден'}")
    
    # Валидация VK токена
    result = validate_vk_token(vk_token, group_id)
    
    if result['valid']:
        logger.info("🎉 Все токены валидны! Бот готов к работе.")
        return True
    else:
        logger.error("❌ Обнаружены проблемы с токенами:")
        for error in result['errors']:
            logger.error(f"   - {error}")
        return False

def generate_token_instructions():
    """Генерация инструкций по получению нового токена"""
    instructions = """
🔧 ИНСТРУКЦИИ ПО ПОЛУЧЕНИЮ VK ТОКЕНА:

1. Перейдите на https://vk.com/apps?act=manage
2. Создайте новое приложение:
   - Название: "VK Bot Fusionbot"
   - Тип: "Standalone-приложение"
3. В настройках приложения:
   - Включите "Open API"
   - Добавьте права: messages, groups, offline
4. Получите токен:
   - Перейдите на https://oauth.vk.com/authorize?client_id=YOUR_APP_ID&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=messages,groups,offline&response_type=token&v=5.199
   - Замените YOUR_APP_ID на ID вашего приложения
   - Авторизуйтесь и скопируйте токен из URL
5. Обновите файл ТОКЕНЫ.env:
   VK_TOKEN=ваш_новый_токен
   VK_GROUP_ID=ваш_group_id

💡 Альтернативный способ:
- Используйте VK Admin для получения токена группы
- Или создайте бота через @BotFather в VK
"""
    print(instructions)

if __name__ == "__main__":
    print("🔍 VK Token Validator")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        generate_token_instructions()
        sys.exit(0)
    
    success = check_current_tokens()
    
    if not success:
        print("\n" + "=" * 50)
        generate_token_instructions()
        sys.exit(1)
    
    print("\n✅ Валидация завершена успешно!")

