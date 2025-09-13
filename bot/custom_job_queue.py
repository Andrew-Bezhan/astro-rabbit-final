"""
Кастомная реализация JobQueue с правильными настройками часового пояса
"""

from telegram.ext import JobQueue as TelegramJobQueue
import pytz

class CustomJobQueue(TelegramJobQueue):
    """Кастомная реализация JobQueue с явным указанием часового пояса"""
    
    def __init__(self):
        # В новой версии python-telegram-bot просто инициализируем базовый класс
        super().__init__()
        
        # Настраиваем timezone для scheduler после инициализации
        if hasattr(self, 'scheduler'):
            self.scheduler.configure(timezone=pytz.UTC)
