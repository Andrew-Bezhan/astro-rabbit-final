"""
Главный файл запуска Астробота
Точка входа в приложение
"""

import os
import asyncio
import signal
import sys
from dotenv import load_dotenv

from bot.telegram_bot import AstroBot
from utils.logger import setup_logger

# Загружаем переменные окружения
load_dotenv()

# Настраиваем логирование
logger = setup_logger()


async def main():
    """Основная функция запуска бота"""
    
    logger.info("🚀 Запуск Астробота...")
    
    # Инициализируем базу данных
    try:
        from database.connection import init_database
        init_database()
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        return
    
    # Проверяем наличие критически важных переменных окружения
    critical_env = ['TELEGRAM_BOT_TOKEN']
    missing_critical = [var for var in critical_env if not os.getenv(var)]
    
    if missing_critical:
        logger.error(f"❌ Отсутствуют критически важные переменные окружения: {', '.join(missing_critical)}")
        return
    
    # Проверяем дополнительные переменные (не критичные для запуска)
    optional_env = ['OPENAI_API_KEY', 'QDRANT_API_KEY', 'NEWSDATA_API_KEY']
    missing_optional = [var for var in optional_env if not os.getenv(var)]
    
    if missing_optional:
        logger.warning(f"⚠️ Отсутствуют дополнительные переменные окружения: {', '.join(missing_optional)}")
        logger.warning("⚠️ Некоторые функции могут быть недоступны")
    
    bot = None
    try:
        # Создаем и запускаем бота
        bot = AstroBot()
        
        # Создаем событие для остановки
        stop_event = asyncio.Event()
        
        # Настройка обработчика сигналов для корректной остановки
        def signal_handler():
            logger.info("⏹️ Получен сигнал остановки")
            stop_event.set()
        
        # Регистрируем обработчики сигналов
        if sys.platform != 'win32':
            loop = asyncio.get_running_loop()
            loop.add_signal_handler(signal.SIGINT, signal_handler)
            loop.add_signal_handler(signal.SIGTERM, signal_handler)
        
        # Запускаем бота
        await bot.start()
        logger.info("✅ Астробот успешно запущен!")
        
        # Ждем сигнал остановки
        try:
            await stop_event.wait()
        except KeyboardInterrupt:
            logger.info("⏹️ Получен сигнал остановки (Ctrl+C)")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
    finally:
        if bot:
            try:
                await bot.stop()
            except Exception as e:
                logger.error(f"❌ Ошибка при остановке бота: {e}")
        logger.info("🛑 Астробот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Программа прервана пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")