"""
Конфигурация APScheduler для Telegram бота
"""

from pytz import UTC
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor

def get_scheduler_config():
    """
    Возвращает конфигурацию APScheduler с явным указанием часового пояса
    """
    jobstores = {
        'default': MemoryJobStore()
    }
    
    executors = {
        'default': ThreadPoolExecutor(20),
        'processpool': ProcessPoolExecutor(5)
    }
    
    job_defaults = {
        'coalesce': False,
        'max_instances': 3,
        'timezone': 'UTC'  # Явно указываем UTC как строку
    }

    return {
        'jobstores': jobstores,
        'executors': executors,
        'job_defaults': job_defaults,
        'timezone': 'UTC'  # Явно указываем UTC как строку
    }

def create_scheduler():
    """
    Создает и настраивает экземпляр APScheduler
    """
    scheduler = AsyncIOScheduler(**get_scheduler_config())
    return scheduler
