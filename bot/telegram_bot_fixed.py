"""
Исправленный модуль Telegram бота Астробота
Использует простой подход без Application для совместимости с Python 3.13
"""

import asyncio
import logging
from typing import Optional

from telegram import Bot, Update
from telegram.error import TelegramError

from .handlers.main_router import MainRouter
from utils.config import load_config
from utils.logger import setup_logger
from database.connection import init_database

logger = setup_logger()


class AstroBot:
    """Основной класс Telegram бота Астробота"""
    
    def __init__(self):
        """Инициализация бота"""
        self.config = load_config()
        self.bot: Optional[Bot] = None
        self.handlers: Optional[MainRouter] = None
        self.running = False
        
        # Проверяем наличие токена
        if not self.config.bot.token:
            logger.error("❌ Отсутствует токен Telegram бота в .env файле")
            raise ValueError("Telegram bot token is required")
        
        # Создаем Bot напрямую
        self.bot = Bot(token=self.config.bot.token)
        
        # Инициализируем обработчики
        self.handlers = MainRouter()
        
        # Хранилище контекстов пользователей
        self.user_contexts = {}
        
        logger.info("🤖 AstroBot инициализирован")
    
    async def start(self):
        """Запуск бота"""
        try:
            if not self.bot:
                logger.error("❌ Bot не инициализирован")
                return
            
            # Получаем информацию о боте
            me = await self.bot.get_me()
            logger.info(f"🚀 Запуск бота @{me.username} ({me.first_name})")
            
            # Очищаем webhook и ждем немного
            await self.bot.delete_webhook(drop_pending_updates=True)
            await asyncio.sleep(2)  # Даем время серверам Telegram обработать
            
            # Получаем последний update_id с retry логикой
            last_update_id = 0
            for attempt in range(3):
                try:
                    updates = await self.bot.get_updates(limit=1)
                    last_update_id = updates[-1].update_id if updates else 0
                    break
                except TelegramError as e:
                    if "conflict" in str(e).lower():
                        logger.warning(f"⚠️ Конфликт при получении updates, попытка {attempt + 1}/3")
                        await asyncio.sleep(5 * (attempt + 1))  # Экспоненциальная задержка
                    else:
                        raise
            
            self.running = True
            logger.info("✅ Бот запущен и готов к работе")
            
            # Основной цикл polling
            while self.running:
                try:
                    # Получаем обновления
                    updates = await self.bot.get_updates(
                        offset=last_update_id + 1,
                        timeout=30
                    )
                    
                    for update in updates:
                        last_update_id = update.update_id
                        await self._handle_update(update)
                        
                except TelegramError as e:
                    if "conflict" in str(e).lower():
                        logger.warning(f"⚠️ Конфликт Telegram API: {e}")
                        logger.info("🔄 Пересоздаем подключение через 10 секунд...")
                        await asyncio.sleep(10)
                        # Пересоздаем бота для решения конфликта
                        await self.bot.close()
                        self.bot = Bot(token=self.config.bot.token)
                        await self.bot.delete_webhook(drop_pending_updates=True)
                        await asyncio.sleep(2)
                    else:
                        logger.error(f"❌ Ошибка Telegram API: {e}")
                        await asyncio.sleep(5)  # Ждем перед повтором
                except Exception as e:
                    logger.error(f"❌ Неожиданная ошибка: {e}")
                    await asyncio.sleep(5)
                    
        except KeyboardInterrupt:
            logger.info("🛑 Получен сигнал остановки")
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске бота: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Остановка бота"""
        try:
            self.running = False
            if self.bot:
                await self.bot.close()
            logger.info("✅ Бот остановлен")
        except Exception as e:
            logger.error(f"❌ Ошибка при остановке бота: {e}")
    
    async def _handle_update(self, update: Update):
        """Обработка обновления"""
        try:
            if update.message:
                await self._handle_message(update.message)
            elif update.callback_query:
                await self._handle_callback_query(update.callback_query)
        except Exception as e:
            logger.error(f"❌ Ошибка обработки обновления: {e}")
    
    async def _handle_message(self, message):
        """Обработка сообщения"""
        try:
            text = message.text
            chat_id = message.chat_id
            user_id = message.from_user.id
            
            # Создаем объект Update для совместимости с обработчиками
            update = Update(
                update_id=0,
                message=message
            )
            
            # Получаем или создаем контекст пользователя
            if user_id not in self.user_contexts:
                class DummyContext:
                    def __init__(self, bot):
                        self.bot = bot
                        self.user_data = {}
                
                self.user_contexts[user_id] = DummyContext(self.bot)
            
            context = self.user_contexts[user_id]
            
            # Роутинг команд
            if text and text.startswith('/'):
                command = text.split()[0]
                
                if command == '/start':
                    await self.handlers.start_command(update, context)
                elif command == '/help':
                    await self.handlers.help_command(update, context)
                elif command == '/zodiac':
                    await self.handlers.zodiac_command(update, context)
                elif command == '/forecast':
                    await self.handlers.forecast_command(update, context)
                elif command == '/compatibility':
                    await self.handlers.compatibility_command(update, context)
                elif command == '/daily':
                    await self.handlers.daily_command(update, context)
                elif command == '/companies':
                    await self.handlers.companies_command(update, context)
                elif command == '/cabinet':
                    await self.handlers.cabinet_command(update, context)
                elif command == '/tariffs':
                    await self.handlers.tariffs_command(update, context)
                else:
                    await self.handlers.message_handler(update, context)
            else:
                # Обычное сообщение
                logger.info(f"📝 Обрабатываем текстовое сообщение: '{text}' от пользователя {user_id}")
                await self.handlers.message_handler(update, context)
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения: {e}")
            try:
                await message.reply_text("❌ Произошла ошибка при обработке сообщения.")
            except:
                pass
    
    async def _handle_callback_query(self, callback_query):
        """Обработка callback запроса"""
        try:
            callback_data = callback_query.data
            
            # Создаем объект Update для совместимости с обработчиками
            update = Update(
                update_id=0,
                callback_query=callback_query
            )
            
            # Получаем или создаем контекст пользователя
            user_id = callback_query.from_user.id
            if user_id not in self.user_contexts:
                class DummyContext:
                    def __init__(self, bot):
                        self.bot = bot
                        self.user_data = {}
                
                self.user_contexts[user_id] = DummyContext(self.bot)
            
            context = self.user_contexts[user_id]
            
            # Роутинг callback'ов
            if callback_data == "main_menu":
                await self.handlers.start_command(update, context)
            elif callback_data == "companies":
                await self.handlers.companies_command(update, context)
            elif callback_data == "zodiac":
                await self.handlers.zodiac_command(update, context)
            elif callback_data == "forecast":
                await self.handlers.forecast_command(update, context)
            elif callback_data == "compatibility":
                await self.handlers.compatibility_command(update, context)
            elif callback_data == "daily":
                await self.handlers.daily_command(update, context)
            elif callback_data == "settings":
                await self.handlers.cabinet_command(update, context)
            elif callback_data.startswith("zodiac_"):
                await self.handlers.callback_handler(update, context)
            elif callback_data.startswith("compatibility_"):
                await self.handlers.callback_handler(update, context)
            elif callback_data.startswith("daily_"):
                await self.handlers.callback_handler(update, context)
            else:
                await self.handlers.callback_handler(update, context)
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки callback: {e}")
            try:
                await callback_query.answer("❌ Произошла ошибка при обработке запроса.")
            except:
                pass
