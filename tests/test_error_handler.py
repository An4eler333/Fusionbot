"""
Тесты для системы обработки ошибок
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from error_handler import (
    ErrorHandler, DataValidator, SafeExecutor,
    ErrorSeverity, ErrorCategory,
    ValidationError, VKAPIError, DatabaseError, AISystemError
)

class TestErrorHandler:
    """Тесты для ErrorHandler"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.error_handler = ErrorHandler()
    
    def test_handle_low_error(self):
        """Тест обработки незначительной ошибки"""
        error = ValueError("Test error")
        result = self.error_handler.handle_error(
            error, 
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW
        )
        
        assert result is True
        assert len(self.error_handler.error_history) == 1
        assert self.error_handler.error_counts["validation_ValueError"] == 1
    
    def test_handle_medium_error(self):
        """Тест обработки средней ошибки"""
        error = VKAPIError("API error")
        result = self.error_handler.handle_error(
            error,
            category=ErrorCategory.VK_API,
            severity=ErrorSeverity.MEDIUM
        )
        
        assert result is True
        assert len(self.error_handler.error_history) == 1
    
    def test_handle_high_error(self):
        """Тест обработки серьезной ошибки"""
        error = DatabaseError("Database connection failed")
        result = self.error_handler.handle_error(
            error,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH
        )
        
        assert result is True
        assert len(self.error_handler.error_history) == 1
    
    def test_handle_critical_error(self):
        """Тест обработки критической ошибки"""
        error = Exception("Critical system failure")
        result = self.error_handler.handle_error(
            error,
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.CRITICAL
        )
        
        assert result is False  # Критические ошибки останавливают обработку
        assert len(self.error_handler.error_history) == 1
    
    def test_error_statistics(self):
        """Тест получения статистики ошибок"""
        # Добавляем несколько ошибок
        self.error_handler.handle_error(
            ValueError("Error 1"),
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW
        )
        self.error_handler.handle_error(
            VKAPIError("Error 2"),
            category=ErrorCategory.VK_API,
            severity=ErrorSeverity.MEDIUM
        )
        
        stats = self.error_handler.get_error_statistics()
        
        assert stats['total_errors'] == 2
        assert 'validation_ValueError' in stats['error_counts']
        assert 'vk_api_VKAPIError' in stats['error_counts']
        assert len(stats['recent_errors']) == 2

class TestDataValidator:
    """Тесты для DataValidator"""
    
    def test_validate_vk_token_valid(self):
        """Тест валидации корректного VK токена"""
        valid_token = "vk1.a.valid_token_string_here_very_long_and_secure"
        assert DataValidator.validate_vk_token(valid_token) is True
    
    def test_validate_vk_token_invalid_format(self):
        """Тест валидации некорректного формата токена"""
        with pytest.raises(ValidationError, match="Неверный формат VK токена"):
            DataValidator.validate_vk_token("invalid_token")
    
    def test_validate_vk_token_empty(self):
        """Тест валидации пустого токена"""
        with pytest.raises(ValidationError, match="Токен не может быть пустым"):
            DataValidator.validate_vk_token("")
    
    def test_validate_vk_token_short(self):
        """Тест валидации короткого токена"""
        with pytest.raises(ValidationError, match="Токен слишком короткий"):
            DataValidator.validate_vk_token("vk1.a.short")
    
    def test_validate_peer_id_valid(self):
        """Тест валидации корректного peer_id"""
        assert DataValidator.validate_peer_id(2000000001) is True
        assert DataValidator.validate_peer_id(123456789) is True
    
    def test_validate_peer_id_invalid(self):
        """Тест валидации некорректного peer_id"""
        with pytest.raises(ValidationError):
            DataValidator.validate_peer_id(-1)
        
        with pytest.raises(ValidationError):
            DataValidator.validate_peer_id(0)
    
    def test_validate_message_text_valid(self):
        """Тест валидации корректного текста сообщения"""
        valid_text = "Привет! Это обычное сообщение."
        assert DataValidator.validate_message_text(valid_text) is True
    
    def test_validate_message_text_too_long(self):
        """Тест валидации слишком длинного сообщения"""
        long_text = "a" * 5000  # Больше 4096 символов
        with pytest.raises(ValidationError, match="Сообщение слишком длинное"):
            DataValidator.validate_message_text(long_text)
    
    def test_validate_message_text_dangerous_content(self):
        """Тест валидации опасного контента"""
        dangerous_text = "<script>alert('xss')</script>"
        with pytest.raises(ValidationError, match="потенциально опасный контент"):
            DataValidator.validate_message_text(dangerous_text)
    
    def test_validate_user_id_valid(self):
        """Тест валидации корректного user_id"""
        assert DataValidator.validate_user_id(123456789) is True
    
    def test_validate_user_id_invalid(self):
        """Тест валидации некорректного user_id"""
        with pytest.raises(ValidationError):
            DataValidator.validate_user_id(-1)
        
        with pytest.raises(ValidationError):
            DataValidator.validate_user_id(0)

class TestSafeExecutor:
    """Тесты для SafeExecutor"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.error_handler = ErrorHandler()
        self.safe_executor = SafeExecutor(self.error_handler)
    
    def test_safe_execute_success(self):
        """Тест успешного выполнения функции"""
        def test_func(x, y):
            return x + y
        
        result = self.safe_executor.safe_execute_sync(
            test_func, 5, 3,
            category=ErrorCategory.VALIDATION
        )
        
        assert result == 8
        assert len(self.error_handler.error_history) == 0
    
    def test_safe_execute_error(self):
        """Тест выполнения функции с ошибкой"""
        def test_func():
            raise ValueError("Test error")
        
        result = self.safe_executor.safe_execute_sync(
            test_func,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW
        )
        
        assert result is None
        assert len(self.error_handler.error_history) == 1
    
    @pytest.mark.asyncio
    async def test_safe_execute_async_success(self):
        """Тест успешного асинхронного выполнения"""
        async def test_async_func(x, y):
            await asyncio.sleep(0.01)  # Имитация асинхронной операции
            return x * y
        
        result = await self.safe_executor.safe_execute(
            test_async_func, 4, 5,
            category=ErrorCategory.VALIDATION
        )
        
        assert result == 20
        assert len(self.error_handler.error_history) == 0
    
    @pytest.mark.asyncio
    async def test_safe_execute_async_error(self):
        """Тест асинхронного выполнения с ошибкой"""
        async def test_async_func():
            await asyncio.sleep(0.01)
            raise AISystemError("AI system error")
        
        result = await self.safe_executor.safe_execute(
            test_async_func,
            category=ErrorCategory.AI_SYSTEM,
            severity=ErrorSeverity.MEDIUM
        )
        
        assert result is None
        assert len(self.error_handler.error_history) == 1

class TestIntegration:
    """Интеграционные тесты"""
    
    def test_error_handling_workflow(self):
        """Тест полного workflow обработки ошибок"""
        error_handler = ErrorHandler()
        validator = DataValidator()
        executor = SafeExecutor(error_handler)
        
        # Тестируем валидацию с ошибкой
        def validate_and_process(data):
            validator.validate_vk_token(data)
            return "processed"
        
        # Выполняем с некорректными данными
        result = executor.safe_execute_sync(
            validate_and_process,
            "invalid_token",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM
        )
        
        assert result is None
        assert len(error_handler.error_history) == 1
        
        # Проверяем статистику
        stats = error_handler.get_error_statistics()
        assert stats['total_errors'] == 1
        assert 'validation_ValidationError' in stats['error_counts']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

