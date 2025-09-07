"""
OpenAI API клиент для астрологических вычислений
Замена Gemini согласно требованиям пользователя
"""

import os
from typing import Dict, Any, Optional, Union
from datetime import datetime
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False

from utils.config import load_config
from utils.logger import setup_logger

logger = setup_logger()


class OpenAIAstroClient:
    """Клиент для работы с OpenAI API"""
    
    def __init__(self):
        """Инициализация OpenAI клиента"""
        self.config = load_config()
        self.client: Optional[Any] = None
        
        try:
            # Проверяем доступность OpenAI
            if not OPENAI_AVAILABLE or not openai:
                raise ImportError("OpenAI SDK не установлен")
            
            # Настраиваем OpenAI API
            self.client = openai.OpenAI(api_key=self.config.openai.api_key)
            logger.info("🔮 OpenAI астрологический клиент инициализирован")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации OpenAI: {e}")
            self.client = None
    
    def get_birth_chart(self, birth_date: datetime, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Создание натальной карты через OpenAI
        
        Args:
            birth_date (datetime): Дата рождения
            latitude (float): Широта места рождения
            longitude (float): Долгота места рождения
            
        Returns:
            Dict[str, Any]: Данные натальной карты
        """
        if not OPENAI_AVAILABLE or not self.config.openai.api_key or not self.client:
            logger.warning("⚠️ OpenAI недоступен, используем базовую карту")
            return self._get_fallback_chart(birth_date, latitude, longitude)
        
        try:
            prompt = f"""
            Создай натальную карту в JSON формате для:
            Дата: {birth_date.strftime('%Y-%m-%d %H:%M')}
            Координаты: {latitude}, {longitude}
            
            Верни JSON с полями:
            - sun_sign: знак солнца
            - moon_sign: знак луны  
            - rising_sign: восходящий знак
            - planets: позиции планет
            - houses: астрологические дома
            - aspects: аспекты между планетами
            
            Ответ должен быть только валидный JSON без дополнительного текста.
            """
            
            # Используем OpenAI для генерации натальной карты
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ты профессиональный астролог. Отвечай только валидным JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Парсим JSON ответ
            try:
                chart_data = json.loads(content)
                logger.info("✅ Натальная карта создана через OpenAI")
                return chart_data
            except json.JSONDecodeError:
                logger.warning("⚠️ Ошибка парсинга JSON от OpenAI")
                return self._get_fallback_chart(birth_date, latitude, longitude)
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания натальной карты через OpenAI: {e}")
            return self._get_fallback_chart(birth_date, latitude, longitude)
    
    def _get_fallback_chart(self, birth_date: datetime, latitude: float, longitude: float) -> Dict[str, Any]:
        """Базовая натальная карта при недоступности API"""
        from utils.helpers import get_zodiac_sign
        
        sun_sign = get_zodiac_sign(birth_date.month, birth_date.day)
        
        return {
            "sun_sign": sun_sign,
            "moon_sign": sun_sign,  # Упрощение
            "rising_sign": sun_sign,  # Упрощение
            "birth_date": birth_date.isoformat(),
            "coordinates": {"latitude": latitude, "longitude": longitude},
            "planets": {
                "sun": {"sign": sun_sign, "degree": 15},
                "moon": {"sign": sun_sign, "degree": 10},
                "mercury": {"sign": sun_sign, "degree": 20},
                "venus": {"sign": sun_sign, "degree": 25},
                "mars": {"sign": sun_sign, "degree": 5}
            },
            "houses": {f"house_{i}": sun_sign for i in range(1, 13)},
            "aspects": []
        }
    
    async def generate_horoscope(self, prompt: str, max_tokens: int = 1500) -> str:
        """
        Генерация гороскопа через OpenAI
        
        Args:
            prompt (str): Промпт для генерации
            max_tokens (int): Максимальное количество токенов
            
        Returns:
            str: Сгенерированный гороскоп
        """
        if not OPENAI_AVAILABLE or not self.config.openai.api_key or not self.client:
            logger.warning("⚠️ OpenAI недоступен")
            return "⚠️ Сервис временно недоступен. Попробуйте позже."
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ты профессиональный астролог AstroRabbit. Создаваешь качественные астрологические прогнозы на русском языке."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            if content:
                logger.info("✅ Гороскоп сгенерирован через OpenAI")
                return content.strip()
            else:
                logger.warning("⚠️ Пустой ответ от OpenAI")
                return "⚠️ Не удалось сгенерировать прогноз. Попробуйте позже."
                
        except Exception as e:
            logger.error(f"❌ Ошибка генерации гороскопа через OpenAI: {e}")
            return f"⚠️ Ошибка генерации: {str(e)}"
    
    async def analyze_compatibility(self, person1_data: Dict[str, Any], 
                                  person2_data: Dict[str, Any]) -> str:
        """
        Анализ совместимости через OpenAI
        
        Args:
            person1_data (Dict): Данные первого человека
            person2_data (Dict): Данные второго человека
            
        Returns:
            str: Анализ совместимости
        """
        if not OPENAI_AVAILABLE or not self.config.openai.api_key or not self.client:
            return "⚠️ Сервис анализа совместимости временно недоступен."
        
        try:
            prompt = f"""
            Проанализируй астрологическую совместимость:
            
            Человек 1: {person1_data.get('sun_sign', 'неизвестно')}
            Человек 2: {person2_data.get('sun_sign', 'неизвестно')}
            
            Дай подробный анализ совместимости этих знаков зодиака.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ты эксперт по астрологической совместимости. Даешь точные и полезные анализы отношений."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            if content:
                return content.strip()
            else:
                return "⚠️ Не удалось проанализировать совместимость."
                
        except Exception as e:
            logger.error(f"❌ Ошибка анализа совместимости через OpenAI: {e}")
            return f"⚠️ Ошибка анализа: {str(e)}"
    
    def generate_astro_analysis(self, chart_data: Dict[str, Any], analysis_type: str) -> str:
        """
        Генерация астрологического анализа через OpenAI
        
        Args:
            chart_data (Dict): Данные натальной карты
            analysis_type (str): Тип анализа
            
        Returns:
            str: Астрологический анализ
        """
        if not OPENAI_AVAILABLE or not self.config.openai.api_key or not self.client:
            return "Астрологический анализ недоступен (OpenAI API не настроен)"
        
        try:
            # Определяем тип анализа
            analysis_prompts = {
                "personality": "Проанализируй личность по натальной карте",
                "business": "Дай бизнес-прогноз на основе астрологических данных", 
                "compatibility": "Проанализируй совместимость",
                "daily": "Создай ежедневный астрологический прогноз",
                "detailed": "Сделай детальный астрологический анализ"
            }
            
            base_prompt = analysis_prompts.get(analysis_type, "Сделай астрологический анализ")
            
            import json
            prompt = f"""
            {base_prompt} на основе следующих астрологических данных:
            
            {json.dumps(chart_data, ensure_ascii=False, indent=2)}
            
            КРИТИЧЕСКИ ВАЖНО - ФОРМАТИРОВАНИЕ ДЛЯ TELEGRAM:
            - НИКОГДА не используй HTML-теги: <p>, <h1>, <h2>, <h3>, <h4>, <b>, <i>, <ul>, <li>, <hr>, <div>
            - НИКОГДА не используй Markdown: **, __, ##, ###, ---
            - Используй ТОЛЬКО обычный текст с эмодзи
            - Заголовки оформляй: "🌟 Название раздела"
            - Списки оформляй: "• Пункт списка"
            - После каждого раздела добавляй пустую строку
            
            ОБЯЗАТЕЛЬНЫЕ ЭМОДЗИ:
            - 🌟 для заголовков и важных моментов
            - ⭐ для ключевых характеристик
            - 💼 для бизнес-рекомендаций
            - ⚡ для энергичных качеств
            - 🚀 для возможностей развития
            - ⚠️ для рисков и предупреждений
            - 💎 для сильных сторон
            - 🔮 для астрологических предсказаний
            - 📈 для роста и прогресса
            - 🤝 для партнерств и отношений
            - 🎯 для целей и направлений
            - 💡 для инсайтов и идей
            - 🔢 для нумерологических расчетов
            - 🌍 для географических факторов
            - ✨ для заключений и итогов
            
            Предоставь подробный, профессиональный анализ на русском языке.
            """
            
            # Используем OpenAI для генерации анализа
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ты профессиональный астролог AstroRabbit. Создаваешь качественные астрологические анализы на русском языке, строго следуя правилам форматирования для Telegram."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            if content:
                logger.info(f"✅ Астрологический анализ создан через OpenAI ({analysis_type})")
                return content.strip()
            else:
                logger.warning("⚠️ Пустой ответ от OpenAI")
                return "⚠️ Не удалось создать астрологический анализ. Попробуйте позже."
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания астрологического анализа через OpenAI: {e}")
            return f"⚠️ Ошибка анализа: {str(e)}"

    def get_model_info(self) -> Dict[str, Any]:
        """Информация о модели"""
        return {
            "provider": "OpenAI",
            "model": "gpt-4",
            "available": OPENAI_AVAILABLE and bool(self.client),
            "features": ["text_generation", "json_mode", "function_calling"]
        }
