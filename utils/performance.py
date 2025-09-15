# -*- coding: utf-8 -*-
"""
Мониторинг производительности и оптимизация
"""

import time
import asyncio
from typing import Dict, Any, Callable, Optional
from functools import wraps
from utils.logger import setup_logger
from utils.cache import cache_manager

logger = setup_logger()


class PerformanceMonitor:
    """Монитор производительности"""
    
    def __init__(self):
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self.start_time = time.time()
    
    def record_execution_time(self, func_name: str, execution_time: float, 
                            cache_hit: bool = False, error: Optional[str] = None):
        """Запись времени выполнения функции"""
        if func_name not in self.metrics:
            self.metrics[func_name] = {
                'total_calls': 0,
                'total_time': 0.0,
                'cache_hits': 0,
                'errors': 0,
                'avg_time': 0.0,
                'max_time': 0.0,
                'min_time': float('inf')
            }
        
        metrics = self.metrics[func_name]
        metrics['total_calls'] += 1
        metrics['total_time'] += execution_time
        metrics['avg_time'] = metrics['total_time'] / metrics['total_calls']
        metrics['max_time'] = max(metrics['max_time'], execution_time)
        metrics['min_time'] = min(metrics['min_time'], execution_time)
        
        if cache_hit:
            metrics['cache_hits'] += 1
        
        if error:
            metrics['errors'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики производительности"""
        uptime = time.time() - self.start_time
        cache_stats = cache_manager.get_stats()
        
        return {
            'uptime': uptime,
            'functions': self.metrics,
            'cache': cache_stats,
            'total_functions': len(self.metrics),
            'total_calls': sum(m['total_calls'] for m in self.metrics.values()),
            'avg_response_time': sum(m['avg_time'] for m in self.metrics.values()) / len(self.metrics) if self.metrics else 0
        }
    
    def log_performance_summary(self):
        """Логирование сводки по производительности"""
        stats = self.get_stats()
        
        logger.info("📊 СВОДКА ПО ПРОИЗВОДИТЕЛЬНОСТИ:")
        logger.info(f"⏱️  Время работы: {stats['uptime']:.1f}с")
        logger.info(f"🔧 Всего функций: {stats['total_functions']}")
        logger.info(f"📞 Всего вызовов: {stats['total_calls']}")
        logger.info(f"⚡ Среднее время ответа: {stats['avg_response_time']:.3f}с")
        
        # Статистика кэша
        cache = stats['cache']
        logger.info(f"💾 Кэш: {cache['active_items']}/{cache['total_items']} активных записей")
        
        # Топ медленных функций
        slow_functions = sorted(
            self.metrics.items(),
            key=lambda x: x[1]['avg_time'],
            reverse=True
        )[:3]
        
        if slow_functions:
            logger.info("🐌 Самые медленные функции:")
            for func_name, metrics in slow_functions:
                logger.info(f"  • {func_name}: {metrics['avg_time']:.3f}с (вызовов: {metrics['total_calls']})")


# Глобальный экземпляр монитора
performance_monitor = PerformanceMonitor()


def monitor_performance(func_name: Optional[str] = None, log_slow_calls: bool = True, 
                       slow_threshold: float = 1.0):
    """Декоратор для мониторинга производительности"""
    def decorator(func):
        name = func_name or func.__name__
        cache_hit = False
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal cache_hit
            start_time = time.time()
            error = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                execution_time = time.time() - start_time
                performance_monitor.record_execution_time(name, execution_time, cache_hit, error)
                
                if log_slow_calls and execution_time > slow_threshold:
                    logger.warning(f"🐌 Медленный вызов {name}: {execution_time:.3f}с")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            nonlocal cache_hit
            start_time = time.time()
            error = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                execution_time = time.time() - start_time
                performance_monitor.record_execution_time(name, execution_time, cache_hit, error)
                
                if log_slow_calls and execution_time > slow_threshold:
                    logger.warning(f"🐌 Медленный вызов {name}: {execution_time:.3f}с")
        
        # Возвращаем нужную обертку в зависимости от типа функции
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_performance_stats():
    """Логирование статистики производительности"""
    performance_monitor.log_performance_summary()


async def periodic_performance_log(interval: int = 300):
    """Периодическое логирование статистики производительности"""
    while True:
        await asyncio.sleep(interval)
        log_performance_stats()


class RateLimiter:
    """Ограничитель частоты запросов"""
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, user_id: str) -> bool:
        """Проверка, разрешен ли запрос для пользователя"""
        current_time = time.time()
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Удаляем старые запросы
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if current_time - req_time < self.time_window
        ]
        
        # Проверяем лимит
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        # Добавляем текущий запрос
        self.requests[user_id].append(current_time)
        return True
    
    def get_remaining_requests(self, user_id: str) -> int:
        """Получение количества оставшихся запросов"""
        if user_id not in self.requests:
            return self.max_requests
        
        current_time = time.time()
        recent_requests = [
            req_time for req_time in self.requests[user_id]
            if current_time - req_time < self.time_window
        ]
        
        return max(0, self.max_requests - len(recent_requests))


# Глобальные экземпляры
rate_limiter = RateLimiter(max_requests=20, time_window=60)  # 20 запросов в минуту


def rate_limit(user_id_key: str = "user_id"):
    """Декоратор для ограничения частоты запросов"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Извлекаем user_id из аргументов
            user_id = None
            for arg in args:
                if hasattr(arg, user_id_key):
                    user_id = str(getattr(arg, user_id_key))
                    break
            
            if not user_id:
                # Пытаемся найти в kwargs
                user_id = str(kwargs.get(user_id_key, 'anonymous'))
            
            if not rate_limiter.is_allowed(user_id):
                remaining = rate_limiter.get_remaining_requests(user_id)
                raise Exception(f"Превышен лимит запросов. Попробуйте через минуту. Осталось: {remaining}")
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Аналогично для синхронных функций
            user_id = None
            for arg in args:
                if hasattr(arg, user_id_key):
                    user_id = str(getattr(arg, user_id_key))
                    break
            
            if not user_id:
                user_id = str(kwargs.get(user_id_key, 'anonymous'))
            
            if not rate_limiter.is_allowed(user_id):
                remaining = rate_limiter.get_remaining_requests(user_id)
                raise Exception(f"Превышен лимит запросов. Попробуйте через минуту. Осталось: {remaining}")
            
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Экспорт основных функций
__all__ = [
    'PerformanceMonitor',
    'performance_monitor',
    'monitor_performance',
    'log_performance_stats',
    'periodic_performance_log',
    'RateLimiter',
    'rate_limiter',
    'rate_limit'
]
