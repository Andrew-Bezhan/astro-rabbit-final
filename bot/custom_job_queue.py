"""
Кастомная реализация JobQueue с правильными настройками часового пояса
"""

from telegram.ext import JobQueue as TelegramJobQueue
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class CustomJobQueue(TelegramJobQueue):
    """Кастомная реализация JobQueue с явным указанием часового пояса"""
    
    def __init__(self):
        super().__init__()
    
    @property
    def _scheduler_config(self):
        """Переопределяем конфигурацию планировщика"""
        return {
            'timezone': pytz.timezone('UTC'),
            'job_defaults': {
                'coalesce': True,
                'max_instances': 1
            }
        }
    
    def _create_scheduler(self):
        """Создаем планировщик с нашими настройками"""
        scheduler = AsyncIOScheduler()
        scheduler.configure(timezone=pytz.timezone('UTC'))
        return scheduler
