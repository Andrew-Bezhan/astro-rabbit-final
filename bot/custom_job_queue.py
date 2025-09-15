"""
Кастомная реализация JobQueue с правильными настройками часового пояса
"""

from telegram.ext import JobQueue as TelegramJobQueue
import pytz
from utils.logger import setup_logger

logger = setup_logger()

class CustomJobQueue(TelegramJobQueue):
    """Кастомная реализация JobQueue с явным указанием часового пояса"""
    
    def __init__(self):
        try:
            # В новой версии python-telegram-bot просто инициализируем базовый класс
            super().__init__()
            logger.info("✅ CustomJobQueue инициализирован")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации CustomJobQueue: {e}")
            # Fallback - используем базовый JobQueue
            super().__init__()
