"""
Система мониторинга и метрик для VK Бота
"""
import os
import json
import time
import psutil
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Типы метрик"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class Metric:
    """Метрика"""
    name: str
    value: float
    type: MetricType
    timestamp: datetime
    labels: Dict[str, str] = None
    description: str = ""

@dataclass
class HealthCheck:
    """Проверка здоровья системы"""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    timestamp: datetime
    response_time: Optional[float] = None

class MetricsCollector:
    """Сборщик метрик"""
    
    def __init__(self):
        self.metrics: List[Metric] = []
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
        self.timers: Dict[str, List[float]] = {}
        self.lock = threading.Lock()
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Увеличение счетчика"""
        with self.lock:
            key = self._get_metric_key(name, labels)
            self.counters[key] = self.counters.get(key, 0) + value
            
            metric = Metric(
                name=name,
                value=self.counters[key],
                type=MetricType.COUNTER,
                timestamp=datetime.now(),
                labels=labels or {}
            )
            self.metrics.append(metric)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Установка значения gauge"""
        with self.lock:
            key = self._get_metric_key(name, labels)
            self.gauges[key] = value
            
            metric = Metric(
                name=name,
                value=value,
                type=MetricType.GAUGE,
                timestamp=datetime.now(),
                labels=labels or {}
            )
            self.metrics.append(metric)
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Запись значения в гистограмму"""
        with self.lock:
            key = self._get_metric_key(name, labels)
            if key not in self.histograms:
                self.histograms[key] = []
            self.histograms[key].append(value)
            
            metric = Metric(
                name=name,
                value=value,
                type=MetricType.HISTOGRAM,
                timestamp=datetime.now(),
                labels=labels or {}
            )
            self.metrics.append(metric)
    
    def record_timer(self, name: str, duration: float, labels: Dict[str, str] = None):
        """Запись времени выполнения"""
        with self.lock:
            key = self._get_metric_key(name, labels)
            if key not in self.timers:
                self.timers[key] = []
            self.timers[key].append(duration)
            
            metric = Metric(
                name=name,
                value=duration,
                type=MetricType.TIMER,
                timestamp=datetime.now(),
                labels=labels or {}
            )
            self.metrics.append(metric)
    
    def _get_metric_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Получение ключа метрики"""
        if not labels:
            return name
        
        label_str = "_".join([f"{k}={v}" for k, v in sorted(labels.items())])
        return f"{name}_{label_str}"
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Получение сводки метрик"""
        with self.lock:
            summary = {
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'histograms': {
                    name: {
                        'count': len(values),
                        'min': min(values) if values else 0,
                        'max': max(values) if values else 0,
                        'avg': sum(values) / len(values) if values else 0
                    }
                    for name, values in self.histograms.items()
                },
                'timers': {
                    name: {
                        'count': len(values),
                        'min': min(values) if values else 0,
                        'max': max(values) if values else 0,
                        'avg': sum(values) / len(values) if values else 0
                    }
                    for name, values in self.timers.items()
                }
            }
            return summary

class SystemMonitor:
    """Монитор системных ресурсов"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.process = psutil.Process()
    
    def collect_system_metrics(self):
        """Сбор системных метрик"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics_collector.set_gauge('system_cpu_percent', cpu_percent)
            
            # Memory
            memory = psutil.virtual_memory()
            self.metrics_collector.set_gauge('system_memory_percent', memory.percent)
            self.metrics_collector.set_gauge('system_memory_available_mb', memory.available / 1024 / 1024)
            
            # Disk
            disk = psutil.disk_usage('/')
            self.metrics_collector.set_gauge('system_disk_percent', disk.percent)
            self.metrics_collector.set_gauge('system_disk_free_gb', disk.free / 1024 / 1024 / 1024)
            
            # Process metrics
            process_memory = self.process.memory_info()
            self.metrics_collector.set_gauge('process_memory_mb', process_memory.rss / 1024 / 1024)
            self.metrics_collector.set_gauge('process_cpu_percent', self.process.cpu_percent())
            
            # Threads
            self.metrics_collector.set_gauge('process_threads', self.process.num_threads())
            
            # File descriptors (Unix only)
            try:
                self.metrics_collector.set_gauge('process_fds', self.process.num_fds())
            except AttributeError:
                pass  # Windows doesn't have num_fds
            
        except Exception as e:
            logger.error(f"Ошибка сбора системных метрик: {e}")

class HealthChecker:
    """Проверка здоровья системы"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.checks: List[HealthCheck] = []
    
    def add_health_check(self, name: str, check_func, timeout: float = 5.0):
        """Добавление проверки здоровья"""
        def wrapper():
            start_time = time.time()
            try:
                result = check_func()
                response_time = time.time() - start_time
                
                if result:
                    status = "healthy"
                    message = "OK"
                else:
                    status = "degraded"
                    message = "Check failed"
                
                health_check = HealthCheck(
                    name=name,
                    status=status,
                    message=message,
                    timestamp=datetime.now(),
                    response_time=response_time
                )
                
            except Exception as e:
                response_time = time.time() - start_time
                health_check = HealthCheck(
                    name=name,
                    status="unhealthy",
                    message=str(e),
                    timestamp=datetime.now(),
                    response_time=response_time
                )
            
            self.checks.append(health_check)
            return health_check
        
        return wrapper
    
    def check_database_health(self) -> bool:
        """Проверка здоровья базы данных"""
        try:
            from database import db
            # Простая проверка подключения
            db.get_user(999999999)  # Несуществующий пользователь
            return True
        except Exception:
            return False
    
    def check_vk_api_health(self) -> bool:
        """Проверка здоровья VK API"""
        try:
            import vk_api
            # Проверяем что токен установлен
            token = os.getenv('VK_TOKEN')
            if not token:
                return False
            
            # Пробуем создать сессию
            session = vk_api.VkApi(token=token)
            vk = session.get_api()
            vk.users.get()
            return True
        except Exception:
            return False
    
    def check_ai_system_health(self) -> bool:
        """Проверка здоровья ИИ системы"""
        try:
            from ai_system import ai_system
            # Простая проверка что система инициализирована
            return ai_system is not None
        except Exception:
            return False
    
    def get_overall_health(self) -> str:
        """Получение общего состояния здоровья"""
        if not self.checks:
            return "unknown"
        
        latest_checks = {}
        for check in self.checks:
            if check.name not in latest_checks or check.timestamp > latest_checks[check.name].timestamp:
                latest_checks[check.name] = check
        
        statuses = [check.status for check in latest_checks.values()]
        
        if "unhealthy" in statuses:
            return "unhealthy"
        elif "degraded" in statuses:
            return "degraded"
        else:
            return "healthy"

class MonitoringDashboard:
    """Дашборд мониторинга"""
    
    def __init__(self, metrics_collector: MetricsCollector, health_checker: HealthChecker):
        self.metrics_collector = metrics_collector
        self.health_checker = health_checker
        self.start_time = datetime.now()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Получение данных для дашборда"""
        uptime = datetime.now() - self.start_time
        
        return {
            'system_info': {
                'uptime': str(uptime).split('.')[0],
                'start_time': self.start_time.isoformat(),
                'python_version': f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
                'platform': psutil.sys.platform
            },
            'health': {
                'overall_status': self.health_checker.get_overall_health(),
                'checks': [asdict(check) for check in self.health_checker.checks[-10:]]  # Последние 10 проверок
            },
            'metrics': self.metrics_collector.get_metrics_summary(),
            'timestamp': datetime.now().isoformat()
        }
    
    def print_dashboard(self):
        """Вывод дашборда в консоль"""
        data = self.get_dashboard_data()
        
        print("\n" + "="*80)
        print("📊 VK BOT MONITORING DASHBOARD")
        print("="*80)
        
        # System Info
        print(f"⏱️  Uptime: {data['system_info']['uptime']}")
        print(f"🐍 Python: {data['system_info']['python_version']}")
        print(f"💻 Platform: {data['system_info']['platform']}")
        
        # Health
        health_status = data['health']['overall_status']
        health_emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}.get(health_status, "❓")
        print(f"{health_emoji} Health: {health_status.upper()}")
        
        # Metrics
        metrics = data['metrics']
        print(f"\n📈 METRICS:")
        print(f"   Counters: {len(metrics['counters'])}")
        print(f"   Gauges: {len(metrics['gauges'])}")
        print(f"   Histograms: {len(metrics['histograms'])}")
        print(f"   Timers: {len(metrics['timers'])}")
        
        # Top counters
        if metrics['counters']:
            print(f"\n🔢 TOP COUNTERS:")
            sorted_counters = sorted(metrics['counters'].items(), key=lambda x: x[1], reverse=True)[:5]
            for name, value in sorted_counters:
                print(f"   {name}: {value}")
        
        # Top gauges
        if metrics['gauges']:
            print(f"\n📊 TOP GAUGES:")
            sorted_gauges = sorted(metrics['gauges'].items(), key=lambda x: x[1], reverse=True)[:5]
            for name, value in sorted_gauges:
                print(f"   {name}: {value}")
        
        print("="*80)

class MonitoringService:
    """Сервис мониторинга"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.system_monitor = SystemMonitor(self.metrics_collector)
        self.health_checker = HealthChecker(self.metrics_collector)
        self.dashboard = MonitoringDashboard(self.metrics_collector, self.health_checker)
        
        # Настраиваем проверки здоровья
        self._setup_health_checks()
        
        # Флаг работы
        self.running = False
        self.monitoring_task = None
    
    def _setup_health_checks(self):
        """Настройка проверок здоровья"""
        self.health_checker.add_health_check("database", self.health_checker.check_database_health)
        self.health_checker.add_health_check("vk_api", self.health_checker.check_vk_api_health)
        self.health_checker.add_health_check("ai_system", self.health_checker.check_ai_system_health)
    
    async def start_monitoring(self, interval: int = 60):
        """Запуск мониторинга"""
        self.running = True
        logger.info("🚀 Запуск системы мониторинга...")
        
        while self.running:
            try:
                # Собираем системные метрики
                self.system_monitor.collect_system_metrics()
                
                # Выполняем проверки здоровья
                self.health_checker.check_database_health()
                self.health_checker.check_vk_api_health()
                self.health_checker.check_ai_system_health()
                
                # Логируем состояние
                if self.metrics_collector.counters.get('monitoring_cycles', 0) % 10 == 0:
                    self.dashboard.print_dashboard()
                
                self.metrics_collector.increment_counter('monitoring_cycles')
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Ошибка мониторинга: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.running = False
        logger.info("🛑 Остановка системы мониторинга...")
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса мониторинга"""
        return {
            'running': self.running,
            'dashboard_data': self.dashboard.get_dashboard_data()
        }

# Глобальный экземпляр сервиса мониторинга
monitoring_service = MonitoringService()

