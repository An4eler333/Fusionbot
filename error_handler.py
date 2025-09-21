"""
Система обработки ошибок и валидации данных для VK Бота
"""
import logging
import traceback
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Уровни серьезности ошибок"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Категории ошибок"""
    VK_API = "vk_api"
    NETWORK = "network"
    DATABASE = "database"
    AI_SYSTEM = "ai_system"
    VALIDATION = "validation"
    UNKNOWN = "unknown"

@dataclass
class ErrorInfo:
    """Информация об ошибке"""
    error: Exception
    category: ErrorCategory
    severity: ErrorSeverity
    context: Dict[str, Any]
    timestamp: datetime
    traceback: str
    user_id: Optional[int] = None
    peer_id: Optional[int] = None

class ValidationError(Exception):
    """Ошибка валидации данных"""
    pass

class VKAPIError(Exception):
    """Ошибка VK API"""
    pass

class DatabaseError(Exception):
    """Ошибка базы данных"""
    pass

class AISystemError(Exception):
    """Ошибка ИИ системы"""
    pass

class ErrorHandler:
    """Централизованная система обработки ошибок"""
    
    def __init__(self):
        self.error_history: List[ErrorInfo] = []
        self.error_counts: Dict[str, int] = {}
        self.retry_strategies: Dict[ErrorCategory, Callable] = {}
        self._setup_retry_strategies()
    
    def _setup_retry_strategies(self):
        """Настройка стратегий повторных попыток"""
        self.retry_strategies = {
            ErrorCategory.NETWORK: self._retry_network_operation,
            ErrorCategory.VK_API: self._retry_vk_api_operation,
            ErrorCategory.DATABASE: self._retry_database_operation,
            ErrorCategory.AI_SYSTEM: self._retry_ai_operation,
        }
    
    def handle_error(
        self,
        error: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        peer_id: Optional[int] = None,
        retry: bool = True
    ) -> bool:
        """
        Обработка ошибки
        
        Returns:
            bool: True если ошибка была обработана, False если критическая
        """
        if context is None:
            context = {}
        
        # Создаем информацию об ошибке
        error_info = ErrorInfo(
            error=error,
            category=category,
            severity=severity,
            context=context,
            timestamp=datetime.now(),
            traceback=traceback.format_exc(),
            user_id=user_id,
            peer_id=peer_id
        )
        
        # Добавляем в историю
        self.error_history.append(error_info)
        
        # Обновляем счетчики
        error_key = f"{category.value}_{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Логируем ошибку
        self._log_error(error_info)
        
        # Обрабатываем в зависимости от серьезности
        if severity == ErrorSeverity.CRITICAL:
            return self._handle_critical_error(error_info)
        elif severity == ErrorSeverity.HIGH:
            return self._handle_high_error(error_info, retry)
        elif severity == ErrorSeverity.MEDIUM:
            return self._handle_medium_error(error_info, retry)
        else:
            return self._handle_low_error(error_info)
    
    def _log_error(self, error_info: ErrorInfo):
        """Логирование ошибки"""
        log_message = (
            f"❌ {error_info.category.value.upper()} ERROR "
            f"[{error_info.severity.value.upper()}] "
            f"{type(error_info.error).__name__}: {error_info.error}"
        )
        
        if error_info.user_id:
            log_message += f" (User: {error_info.user_id})"
        if error_info.peer_id:
            log_message += f" (Peer: {error_info.peer_id})"
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
            logger.critical(f"Traceback: {error_info.traceback}")
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _handle_critical_error(self, error_info: ErrorInfo) -> bool:
        """Обработка критических ошибок"""
        logger.critical("🚨 КРИТИЧЕСКАЯ ОШИБКА! Требуется вмешательство!")
        
        # Отправляем уведомление администратору
        self._notify_admin(error_info)
        
        # Возвращаем False для остановки обработки
        return False
    
    def _handle_high_error(self, error_info: ErrorInfo, retry: bool) -> bool:
        """Обработка серьезных ошибок"""
        if retry and error_info.category in self.retry_strategies:
            return self.retry_strategies[error_info.category](error_info)
        
        # Fallback обработка
        return self._fallback_handling(error_info)
    
    def _handle_medium_error(self, error_info: ErrorInfo, retry: bool) -> bool:
        """Обработка средних ошибок"""
        if retry and error_info.category in self.retry_strategies:
            return self.retry_strategies[error_info.category](error_info)
        
        return True  # Продолжаем работу
    
    def _handle_low_error(self, error_info: ErrorInfo) -> bool:
        """Обработка незначительных ошибок"""
        return True  # Просто логируем и продолжаем
    
    def _retry_network_operation(self, error_info: ErrorInfo) -> bool:
        """Повторная попытка сетевой операции"""
        logger.info("🔄 Повторная попытка сетевой операции...")
        # Здесь можно добавить логику повторных попыток
        return True
    
    def _retry_vk_api_operation(self, error_info: ErrorInfo) -> bool:
        """Повторная попытка VK API операции"""
        logger.info("🔄 Повторная попытка VK API операции...")
        # Здесь можно добавить логику повторных попыток
        return True
    
    def _retry_database_operation(self, error_info: ErrorInfo) -> bool:
        """Повторная попытка операции с базой данных"""
        logger.info("🔄 Повторная попытка операции с БД...")
        # Здесь можно добавить логику повторных попыток
        return True
    
    def _retry_ai_operation(self, error_info: ErrorInfo) -> bool:
        """Повторная попытка ИИ операции"""
        logger.info("🔄 Повторная попытка ИИ операции...")
        # Здесь можно добавить логику повторных попыток
        return True
    
    def _fallback_handling(self, error_info: ErrorInfo) -> bool:
        """Fallback обработка ошибок"""
        if error_info.category == ErrorCategory.VK_API:
            logger.warning("⚠️  Переход в демо-режим из-за ошибки VK API")
            return True
        elif error_info.category == ErrorCategory.AI_SYSTEM:
            logger.warning("⚠️  Использование локальных ответов ИИ")
            return True
        elif error_info.category == ErrorCategory.DATABASE:
            logger.warning("⚠️  Использование кэшированных данных")
            return True
        
        return True
    
    def _notify_admin(self, error_info: ErrorInfo):
        """Уведомление администратора о критической ошибке"""
        # Здесь можно добавить отправку уведомлений
        logger.critical(f"📧 Уведомление администратора: {error_info.error}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Получение статистики ошибок"""
        return {
            'total_errors': len(self.error_history),
            'error_counts': self.error_counts,
            'recent_errors': [
                {
                    'timestamp': error.timestamp.isoformat(),
                    'category': error.category.value,
                    'severity': error.severity.value,
                    'error': str(error.error)
                }
                for error in self.error_history[-10:]  # Последние 10 ошибок
            ]
        }

class DataValidator:
    """Валидатор данных"""
    
    @staticmethod
    def validate_vk_token(token: str) -> bool:
        """Валидация VK токена"""
        if not token:
            raise ValidationError("Токен не может быть пустым")
        
        if not isinstance(token, str):
            raise ValidationError("Токен должен быть строкой")
        
        if not token.startswith('vk1.a.'):
            raise ValidationError("Неверный формат VK токена")
        
        if len(token) < 50:
            raise ValidationError("Токен слишком короткий")
        
        return True
    
    @staticmethod
    def validate_peer_id(peer_id: int) -> bool:
        """Валидация peer_id"""
        if not isinstance(peer_id, int):
            raise ValidationError("peer_id должен быть числом")
        
        if peer_id <= 0:
            raise ValidationError("peer_id должен быть положительным")
        
        return True
    
    @staticmethod
    def validate_message_text(text: str) -> bool:
        """Валидация текста сообщения"""
        if not isinstance(text, str):
            raise ValidationError("Текст сообщения должен быть строкой")
        
        if len(text) > 4096:
            raise ValidationError("Сообщение слишком длинное")
        
        # Проверка на потенциально опасный контент
        dangerous_patterns = [
            r'<script.*?>',
            r'javascript:',
            r'data:text/html',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValidationError("Сообщение содержит потенциально опасный контент")
        
        return True
    
    @staticmethod
    def validate_user_id(user_id: int) -> bool:
        """Валидация user_id"""
        if not isinstance(user_id, int):
            raise ValidationError("user_id должен быть числом")
        
        if user_id <= 0:
            raise ValidationError("user_id должен быть положительным")
        
        return True
    
    @staticmethod
    def validate_group_id(group_id: int) -> bool:
        """Валидация group_id"""
        if not isinstance(group_id, int):
            raise ValidationError("group_id должен быть числом")
        
        if group_id <= 0:
            raise ValidationError("group_id должен быть положительным")
        
        return True

class SafeExecutor:
    """Безопасный исполнитель операций с обработкой ошибок"""
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
    
    async def safe_execute(
        self,
        func: Callable,
        *args,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Безопасное выполнение функции"""
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            self.error_handler.handle_error(
                e, category=category, severity=severity, context=context
            )
            return None
    
    def safe_execute_sync(
        self,
        func: Callable,
        *args,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Безопасное синхронное выполнение функции"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.error_handler.handle_error(
                e, category=category, severity=severity, context=context
            )
            return None

# Глобальные экземпляры
error_handler = ErrorHandler()
data_validator = DataValidator()
safe_executor = SafeExecutor(error_handler)

