#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Оптимизированная версия запуска бота с мониторингом производительности
"""

import asyncio
import signal
import sys
from utils.logger import setup_logger
from utils.performance import periodic_performance_log, log_performance_stats
from utils.cache import cleanup_cache_periodically
from bot.telegram_bot import AstroBot

logger = setup_logger()


class OptimizedAstroBot:
    """Оптимизированная версия AstroBot с мониторингом производительности"""
    
    def __init__(self):
        # Создаем экземпляр базового бота
        self.bot = AstroBot()
        self.background_tasks = []
    
    async def start(self):
        """Запуск оптимизированного бота"""
        logger.info("🚀 Запуск оптимизированного AstroBot...")
        
        # Запускаем фоновые задачи
        self.background_tasks = [
            asyncio.create_task(periodic_performance_log(interval=600)),  # Каждые 10 минут
            asyncio.create_task(cleanup_cache_periodically(interval=300)),  # Каждые 5 минут
        ]
        
        logger.info("📊 Мониторинг производительности активирован")
        logger.info("💾 Автоочистка кэша активирована")
        
        try:
            # Запускаем основной бот через его экземпляр
            await self.bot.application.run_polling(drop_pending_updates=True)
        except KeyboardInterrupt:
            logger.info("🛑 Получен сигнал остановки")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Очистка ресурсов"""
        logger.info("🧹 Очистка ресурсов...")
        
        # Отменяем фоновые задачи
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Логируем финальную статистику
        try:
            log_performance_stats()
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при логировании статистики: {e}")
        
        logger.info("✅ Очистка завершена")


def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info(f"🛑 Получен сигнал {signum}")
    # Устанавливаем флаг для корректного завершения
    if hasattr(signal_handler, 'shutdown_requested'):
        signal_handler.shutdown_requested = True


async def main():
    """Главная функция"""
    # Инициализируем флаг для корректного завершения
    signal_handler.shutdown_requested = False
    
    # Настраиваем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Создаем и запускаем бота
        bot = OptimizedAstroBot()
        await bot.start()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал прерывания")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)
