# -*- coding: utf-8 -*-
"""
Менеджер сервисов для предотвращения дублирования инициализации
"""

from typing import Optional
from utils.logger import setup_logger

logger = setup_logger()


class ServicesManager:
    """Синглтон-менеджер для управления сервисами бота"""
    
    _instance: Optional['ServicesManager'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_services()
            ServicesManager._initialized = True
    
    def _initialize_services(self):
        """Инициализация всех сервисов один раз"""
        logger.info("🔧 Инициализация менеджера сервисов...")
        
        try:
            # Инициализируем основные сервисы
            from ai_astrologist.astro_agent import AstroAgent
            from ai_astrologist.numerology import NumerologyCalculator
            from news_parser.news_analyzer import NewsAnalyzer
            from embedding.embedding_manager import EmbeddingManager
            
            self.astro_agent = AstroAgent()
            self.numerology = NumerologyCalculator()
            self.news_analyzer = NewsAnalyzer()
            
            # Инициализируем валидатор (опционально)
            try:
                from validation_agent.validator import ValidationAgent
                self.validator = ValidationAgent()
                logger.info("✅ Валидатор инициализирован")
            except Exception as e:
                logger.warning(f"⚠️ Валидатор недоступен: {e}")
                self.validator = None
            
            # Инициализируем embedding manager (опционально)
            try:
                self.embedding_manager = EmbeddingManager()
                logger.info("✅ Embedding manager инициализирован")
            except Exception as e:
                logger.warning(f"⚠️ Embedding manager недоступен: {e}")
                self.embedding_manager = None
            
            logger.info("✅ Все сервисы инициализированы успешно")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации сервисов: {e}")
            raise
    
    @classmethod
    def get_instance(cls) -> 'ServicesManager':
        """Получить экземпляр менеджера сервисов"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
