# -*- coding: utf-8 -*-
"""
Система кэширования для оптимизации производительности
"""

import time
import json
from typing import Any, Optional, Dict
from functools import wraps
import hashlib
from utils.logger import setup_logger

logger = setup_logger()


class CacheManager:
    """Менеджер кэширования"""
    
    def __init__(self, default_ttl: int = 300):  # 5 минут по умолчанию
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Генерация ключа кэша"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        if key not in self.cache:
            return None
        
        cache_item = self.cache[key]
        
        # Проверяем TTL
        if time.time() > cache_item['expires_at']:
            del self.cache[key]
            return None
        
        logger.debug(f"📦 Кэш попадание: {key}")
        return cache_item['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Сохранение значения в кэш"""
        if ttl is None:
            ttl = self.default_ttl
        
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
        
        logger.debug(f"💾 Кэш сохранение: {key} (TTL: {ttl}s)")
    
    def clear(self, pattern: Optional[str] = None) -> None:
        """Очистка кэша"""
        if pattern is None:
            self.cache.clear()
            logger.info("🧹 Весь кэш очищен")
        else:
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self.cache[key]
            logger.info(f"🧹 Кэш очищен по паттерну: {pattern}")
    
    def cleanup_expired(self) -> None:
        """Очистка просроченных записей"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.cache.items()
            if current_time > item['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"🧹 Удалено {len(expired_keys)} просроченных записей из кэша")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        current_time = time.time()
        active_items = sum(
            1 for item in self.cache.values()
            if current_time <= item['expires_at']
        )
        
        return {
            'total_items': len(self.cache),
            'active_items': active_items,
            'expired_items': len(self.cache) - active_items,
            'memory_usage': len(str(self.cache))
        }


# Глобальный экземпляр кэш-менеджера
cache_manager = CacheManager()


def cached(ttl: int = 300, key_prefix: str = ""):
    """Декоратор для кэширования результатов функций"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Генерируем ключ кэша
            cache_key = f"{key_prefix}:{func.__name__}:{cache_manager._generate_key(*args, **kwargs)}"
            
            # Пытаемся получить из кэша
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Выполняем функцию и кэшируем результат
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Генерируем ключ кэша
            cache_key = f"{key_prefix}:{func.__name__}:{cache_manager._generate_key(*args, **kwargs)}"
            
            # Пытаемся получить из кэша
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Выполняем функцию и кэшируем результат
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        # Возвращаем нужную обертку в зависимости от типа функции
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_news_data(ttl: int = 600):  # 10 минут для новостей
    """Специальный декоратор для кэширования новостей"""
    return cached(ttl=ttl, key_prefix="news")


def cache_astro_data(ttl: int = 1800):  # 30 минут для астрологических данных
    """Специальный декоратор для кэширования астрологических данных"""
    return cached(ttl=ttl, key_prefix="astro")


def cache_company_data(ttl: int = 3600):  # 1 час для данных компаний
    """Специальный декоратор для кэширования данных компаний"""
    return cached(ttl=ttl, key_prefix="company")


# Функция для периодической очистки кэша
async def cleanup_cache_periodically(interval: int = 300):
    """Периодическая очистка кэша"""
    while True:
        await asyncio.sleep(interval)
        cache_manager.cleanup_expired()


# Экспорт основных функций
__all__ = [
    'CacheManager',
    'cache_manager',
    'cached',
    'cache_news_data',
    'cache_astro_data',
    'cache_company_data',
    'cleanup_cache_periodically'
]
