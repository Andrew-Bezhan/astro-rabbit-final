"""
Кастомная реализация JobQueue с правильными настройками часового пояса
"""

from telegram.ext import JobQueue as TelegramJobQueue
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class CustomJobQueue(TelegramJobQueue):
    """Кастомная реализация JobQueue с явным указанием часового пояса"""
    
    def __init__(self):
        # Создаем scheduler с правильной конфигурацией timezone
        scheduler = AsyncIOScheduler(
            timezone=pytz.UTC,  # Используем pytz timezone
            job_defaults={
                'coalesce': True,
                'max_instances': 1
            }
        )
        super().__init__(scheduler=scheduler)
