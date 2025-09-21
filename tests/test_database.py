"""
Тесты для системы базы данных
"""
import pytest
import sqlite3
import tempfile
import os
from datetime import datetime

from database import DatabaseManager

class TestDatabaseManager:
    """Тесты для DatabaseManager"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        # Создаем временную базу данных для тестов
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        # Удаляем временную базу данных
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Тест инициализации базы данных"""
        # Проверяем что таблицы созданы
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            
            # Проверяем таблицу users
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            assert cursor.fetchone() is not None
            
            # Проверяем таблицу chat_admins
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_admins'")
            assert cursor.fetchone() is not None
    
    def test_create_or_update_user(self):
        """Тест создания и обновления пользователя"""
        user_id = 123456789
        user_info = {
            'first_name': 'Тест',
            'last_name': 'Пользователь'
        }
        
        # Создаем пользователя
        result = self.db_manager.create_or_update_user(user_id, user_info)
        
        assert result is not None
        assert result['user_id'] == user_id
        assert result['first_name'] == 'Тест'
        assert result['last_name'] == 'Пользователь'
        assert result['experience'] == 0
        assert result['rank_level'] == 1
    
    def test_get_user(self):
        """Тест получения пользователя"""
        user_id = 123456789
        user_info = {
            'first_name': 'Тест',
            'last_name': 'Пользователь'
        }
        
        # Создаем пользователя
        self.db_manager.create_or_update_user(user_id, user_info)
        
        # Получаем пользователя
        user = self.db_manager.get_user(user_id)
        
        assert user is not None
        assert user['user_id'] == user_id
        assert user['first_name'] == 'Тест'
        assert user['last_name'] == 'Пользователь'
    
    def test_get_nonexistent_user(self):
        """Тест получения несуществующего пользователя"""
        user = self.db_manager.get_user(999999999)
        assert user is None
    
    def test_update_existing_user(self):
        """Тест обновления существующего пользователя"""
        user_id = 123456789
        user_info = {
            'first_name': 'Тест',
            'last_name': 'Пользователь'
        }
        
        # Создаем пользователя
        self.db_manager.create_or_update_user(user_id, user_info)
        
        # Обновляем пользователя
        updated_info = {
            'first_name': 'Обновленный',
            'last_name': 'Пользователь'
        }
        result = self.db_manager.create_or_update_user(user_id, updated_info)
        
        assert result is not None
        assert result['first_name'] == 'Обновленный'
        assert result['last_name'] == 'Пользователь'
    
    def test_set_admin(self):
        """Тест установки администратора"""
        user_id = 123456789
        chat_id = 2000000001
        
        # Устанавливаем админа
        self.db_manager.set_admin(user_id, chat_id, is_owner=False)
        
        # Проверяем что админ установлен
        is_admin = self.db_manager.is_admin(user_id, chat_id)
        assert is_admin is True
    
    def test_set_owner(self):
        """Тест установки владельца"""
        user_id = 123456789
        chat_id = 2000000001
        
        # Устанавливаем владельца
        self.db_manager.set_admin(user_id, chat_id, is_owner=True)
        
        # Проверяем что владелец установлен
        is_admin = self.db_manager.is_admin(user_id, chat_id)
        assert is_admin is True
    
    def test_is_admin_nonexistent(self):
        """Тест проверки несуществующего админа"""
        is_admin = self.db_manager.is_admin(999999999, 2000000001)
        assert is_admin is False
    
    def test_get_rank_info(self):
        """Тест получения информации о рангах"""
        # Тестируем все ранги
        for rank_level in range(1, 11):
            rank_info = self.db_manager.get_rank_info(rank_level)
            assert rank_info is not None
            assert 'name' in rank_info
            assert 'emoji' in rank_info
            assert len(rank_info['name']) > 0
            assert len(rank_info['emoji']) > 0
    
    def test_get_rank_info_invalid(self):
        """Тест получения информации о несуществующем ранге"""
        rank_info = self.db_manager.get_rank_info(999)
        assert rank_info is not None
        assert rank_info['name'] == "🥉 Новичок"  # Должен вернуть ранг по умолчанию
    
    def test_get_top_users_empty(self):
        """Тест получения топа пользователей из пустой базы"""
        top_users = self.db_manager.get_top_users()
        assert top_users == []
    
    def test_get_top_users_with_data(self):
        """Тест получения топа пользователей с данными"""
        # Создаем несколько пользователей с разным опытом
        users_data = [
            (111, {'first_name': 'Первый', 'last_name': 'Пользователь'}),
            (222, {'first_name': 'Второй', 'last_name': 'Пользователь'}),
            (333, {'first_name': 'Третий', 'last_name': 'Пользователь'})
        ]
        
        for user_id, user_info in users_data:
            self.db_manager.create_or_update_user(user_id, user_info)
        
        # Обновляем опыт пользователей
        with sqlite3.connect(self.temp_db.name) as conn:
            conn.execute("UPDATE users SET experience = ? WHERE user_id = ?", (100, 111))
            conn.execute("UPDATE users SET experience = ? WHERE user_id = ?", (200, 222))
            conn.execute("UPDATE users SET experience = ? WHERE user_id = ?", (300, 333))
        
        # Получаем топ пользователей
        top_users = self.db_manager.get_top_users(limit=2)
        
        assert len(top_users) == 2
        assert top_users[0]['user_id'] == 333  # Самый высокий опыт
        assert top_users[1]['user_id'] == 222  # Второй по опыту
    
    def test_database_connection_error_handling(self):
        """Тест обработки ошибок подключения к базе данных"""
        # Создаем DatabaseManager с несуществующим путем
        invalid_db = DatabaseManager("/invalid/path/database.db")
        
        # Попытка получить пользователя должна вернуть None
        user = invalid_db.get_user(123)
        assert user is None
    
    def test_sql_injection_protection(self):
        """Тест защиты от SQL инъекций"""
        user_id = 123456789
        malicious_info = {
            'first_name': "'; DROP TABLE users; --",
            'last_name': 'Пользователь'
        }
        
        # Попытка SQL инъекции должна быть безопасной
        result = self.db_manager.create_or_update_user(user_id, malicious_info)
        
        # Проверяем что таблица все еще существует
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            assert cursor.fetchone() is not None
        
        # Проверяем что пользователь создался с экранированным именем
        assert result is not None
        assert result['first_name'] == "'; DROP TABLE users; --"
    
    def test_concurrent_access(self):
        """Тест одновременного доступа к базе данных"""
        import threading
        import time
        
        results = []
        
        def create_user(user_id):
            user_info = {
                'first_name': f'Пользователь{user_id}',
                'last_name': 'Тест'
            }
            result = self.db_manager.create_or_update_user(user_id, user_info)
            results.append(result)
        
        # Создаем несколько потоков
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_user, args=(100 + i,))
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем что все пользователи созданы
        assert len(results) == 5
        for result in results:
            assert result is not None
            assert result['user_id'] in range(100, 105)

class TestDatabaseIntegration:
    """Интеграционные тесты базы данных"""
    
    def test_full_user_lifecycle(self):
        """Тест полного жизненного цикла пользователя"""
        # Создаем временную базу
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        db_manager = DatabaseManager(temp_db.name)
        
        try:
            user_id = 123456789
            user_info = {
                'first_name': 'Интеграционный',
                'last_name': 'Тест'
            }
            
            # 1. Создаем пользователя
            user = db_manager.create_or_update_user(user_id, user_info)
            assert user is not None
            assert user['experience'] == 0
            assert user['rank_level'] == 1
            
            # 2. Получаем пользователя
            retrieved_user = db_manager.get_user(user_id)
            assert retrieved_user is not None
            assert retrieved_user['first_name'] == 'Интеграционный'
            
            # 3. Устанавливаем админа
            chat_id = 2000000001
            db_manager.set_admin(user_id, chat_id, is_owner=True)
            assert db_manager.is_admin(user_id, chat_id) is True
            
            # 4. Получаем информацию о ранге
            rank_info = db_manager.get_rank_info(user['rank_level'])
            assert rank_info is not None
            assert rank_info['name'] == "🥉 Новичок"
            
            # 5. Обновляем опыт пользователя
            with sqlite3.connect(temp_db.name) as conn:
                conn.execute("UPDATE users SET experience = 150, rank_level = 2 WHERE user_id = ?", (user_id,))
            
            # 6. Проверяем обновленный ранг
            updated_user = db_manager.get_user(user_id)
            assert updated_user['experience'] == 150
            assert updated_user['rank_level'] == 2
            
            updated_rank_info = db_manager.get_rank_info(updated_user['rank_level'])
            assert updated_rank_info['name'] == "🏃 Активный"
            
        finally:
            # Очищаем временную базу
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

