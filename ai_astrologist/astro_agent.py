# -*- coding: utf-8 -*-
"""
Основной модуль AI-астролога AstroRabbit
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from ai_astrologist.numerology import NumerologyCalculator
from astrology_api.astro_calculations import AstroCalculations
from utils.config import load_config
from utils.helpers import get_zodiac_sign
from utils.logger import setup_logger

# Подключаем загрузку профилей и расчет метрик из scoring.yaml
from validation_agent import load_scoring_profile, compute_score

logger = setup_logger()

class AstroAgent:
    """AI-агент (астролог) AstroRabbit"""
    def __init__(self):
        """Инициализация агента AstroRabbit"""
        self.config = load_config()
        try:
            from ai_astrologist.openai_client import OpenAIAstroClient
            self.openai_client = OpenAIAstroClient()
            self.numerology = NumerologyCalculator()
            self.astro_calculations = AstroCalculations()
            logger.info("✅ AstroRabbit успешно инициализирован (OpenAI клиент подключен)")
        except Exception as e:
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось инициализировать AI-астролога: {e}")
            raise Exception(f"OpenAI клиент не может быть инициализирован: {e}")

    async def analyze_company_zodiac(self, company_info: Dict[str, Any], news_data: str = "") -> str:
        """
        Анализ знака зодиака компании (краткий астрологический и нумерологический профиль).

        Args:
            company_info (Dict): Информация о компании (название, дата/место регистрации и т.д.)
            news_data (str): Актуальные новости для контекста (необязательный параметр)

        Returns:
            str: Сгенерированный анализ знака зодиака компании
        """
        try:
            # Парсим дату регистрации компании в объект datetime
            registration_date = company_info.get('registration_date')
            if isinstance(registration_date, str):
                date_obj = None
                for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S'):
                    try:
                        date_obj = datetime.strptime(registration_date, fmt)
                        break
                    except ValueError:
                        continue
                if date_obj is None:
                    try:
                        date_obj = datetime.fromisoformat(registration_date)
                    except Exception:
                        date_obj = None
                registration_date = date_obj or datetime(2020, 1, 1)

            # Получаем натальную карту компании (подробные астрологические данные) если возможно
            natal_chart = {}
            if self.astro_calculations and registration_date:
                natal_chart = await self.astro_calculations.get_company_natal_chart(
                    company_info.get('name', ''),
                    registration_date,
                    company_info.get('registration_place', '')
                )

            zodiac_sign = get_zodiac_sign(registration_date) if registration_date else "Неизвестно"

            # Подготовка дополнительной информации (аспекты, элементы) для справки
            astro_info = ""
            if natal_chart:
                basic_info = natal_chart.get('basic_info', {})
                interpretation = natal_chart.get('interpretation', {})
                astro_info = (
                    "\nДетальная астрологическая информация:\n"
                    f"• Элемент: {basic_info.get('element', '')}\n"
                    f"• Управитель: {basic_info.get('ruler', '')}\n"
                    f"• Бизнес-стиль: {interpretation.get('business_style', '')}\n"
                    f"• Финансовые перспективы: {interpretation.get('financial_outlook', '')}\n"
                    f"• Потенциал роста: {interpretation.get('growth_potential', '')}\n"
                    f"• Рекомендуемые сферы: {', '.join(basic_info.get('best_spheres', []))}\n"
                )

            # Формируем входные данные для генерации текста
            chart_data = {
                "company_data": company_info,
                "zodiac_sign": zodiac_sign,
                "astro_info": astro_info,
                "news_data": news_data[:2000] if news_data else ""
            }

            if not self.openai_client:
                raise Exception("OpenAI клиент не инициализирован")

            # Генерируем анализ с помощью LLM
            result = self.openai_client.generate_astro_analysis(chart_data, "zodiac_info")
            logger.info(f"✨ Завершён анализ знака зодиака для компании \"{company_info.get('name', '')}\"")

            if result:
                # Подключаем систему метрик для оценки результата
                try:
                    profile = load_scoring_profile("zodiac_info")
                    local_score = compute_score(result, profile)
                    critic_feedback = self.openai_client.criticize_answer("zodiac_info", result, profile)
                    logger.info(
                        f"📊 Локальная оценка: {local_score['score']}/10 — "
                        f"Оценка критика: {critic_feedback.get('score', 'N/A')}/10, "
                        f"Комментарий критика: {critic_feedback.get('comment', '')}"
                    )
                except Exception as me:
                    logger.warning(f"⚠️ Не удалось вычислить метрики для zodiac_info: {me}")
                return result
            else:
                return "🔮 Астрологический анализ завершён. Получены уникальные инсайты для вашей компании."
        except Exception as e:
            logger.error(f"❌ Ошибка при анализе знака зодиака компании: {e}")
            raise Exception(f"Ошибка анализа знака зодиака: {e}")

    async def generate_business_forecast(self, company_data: Dict[str, Any], astrology_data: str = "", news_data: str = "") -> str:
        """
        Генерация полного бизнес-прогноза для компании.

        Args:
            company_data (Dict): Полные данные компании
            astrology_data (str): Предварительные астрологические данные (например, интерпретации натальной карты)
            news_data (str): Сводка актуальных новостей для отрасли

        Returns:
            str: Сгенерированный бизнес-прогноз для компании
        """
        try:
            # Определяем знаки зодиака на основе дат
            company_zodiac = self._get_zodiac_safe(company_data.get('registration_date'))
            owner_zodiac = self._get_zodiac_safe(company_data.get('owner_birth_date'))
            director_zodiac = self._get_zodiac_safe(company_data.get('director_birth_date'))

            # Вычисляем нумерологические числа владельца и директора компании
            owner_numerology = 0
            director_numerology = 0
            if company_data.get('owner_name'):
                owner_numerology = self.numerology.calculate_name_number(company_data['owner_name'])
            if company_data.get('director_name'):
                director_numerology = self.numerology.calculate_name_number(company_data['director_name'])

            # Подготавливаем данные для LLM
            chart_data = {
                "company_data": company_data,
                "company_zodiac": company_zodiac,
                "owner_zodiac": owner_zodiac,
                "director_zodiac": director_zodiac,
                "owner_numerology": owner_numerology,
                "director_numerology": director_numerology,
                "astrology_data": astrology_data,
                "news_data": news_data[:2000] if news_data else ""
            }

            if not self.openai_client:
                raise Exception("OpenAI клиент не инициализирован")

            result = self.openai_client.generate_astro_analysis(chart_data, "business_forecast")
            logger.info(f"📊 Бизнес-прогноз для \"{company_data.get('name', '')}\" сгенерирован")

            if result:
                try:
                    profile = load_scoring_profile("business_forecast")
                    local_score = compute_score(result, profile)
                    critic_feedback = self.openai_client.criticize_answer("business_forecast", result, profile)
                    logger.info(
                        f"📊 Локальная оценка: {local_score['score']}/10 — "
                        f"Оценка критика: {critic_feedback.get('score', 'N/A')}/10, "
                        f"Комментарий критика: {critic_feedback.get('comment', '')}"
                    )
                except Exception as me:
                    logger.warning(f"⚠️ Не удалось вычислить метрики для business_forecast: {me}")
                return result
            else:
                return "📊 Бизнес-прогноз готов. Получены стратегические рекомендации для развития компании."
        except Exception as e:
            logger.error(f"❌ Ошибка генерации бизнес-прогноза: {e}")
            raise Exception(f"Ошибка генерации бизнес-прогноза: {e}")

    async def analyze_compatibility(self, company_data: Dict[str, Any], object_data: Dict[str, Any], object_type: str) -> str:
        """
        Анализ астрологической и нумерологической совместимости компании с указанным объектом.

        Args:
            company_data (Dict): Данные компании
            object_data (Dict): Данные объекта (человека или другой компании)
            object_type (str): Тип объекта ("сотрудник", "клиент" или "партнер")

        Returns:
            str: Сгенерированный анализ совместимости
        """
        try:
            # Знаки зодиака компании и объекта
            company_zodiac = self._get_zodiac_safe(company_data.get('registration_date'))
            object_zodiac = self._get_zodiac_safe(object_data.get('birth_date'))

            # Нумерологическое число имени объекта
            object_numerology = 0
            if object_data.get('name'):
                object_numerology = self.numerology.calculate_name_number(object_data['name'])

            # Подготавливаем данные для генерации
            chart_data = {
                "company_data": company_data,
                "object_data": object_data,
                "object_type": object_type,
                "company_zodiac": company_zodiac,
                "object_zodiac": object_zodiac,
                "object_numerology": object_numerology
            }

            if not self.openai_client:
                raise Exception("OpenAI клиент не инициализирован")

            result = self.openai_client.generate_astro_analysis(chart_data, "compatibility")
            logger.info(f"🤝 Анализ совместимости ({object_type}) выполнен")

            if result:
                try:
                    profile = load_scoring_profile("compatibility")
                    local_score = compute_score(result, profile)
                    critic_feedback = self.openai_client.criticize_answer("compatibility", result, profile)
                    logger.info(
                        f"🤝 Локальная оценка: {local_score['score']}/10 — "
                        f"Оценка критика: {critic_feedback.get('score', 'N/A')}/10, "
                        f"Комментарий критика: {critic_feedback.get('comment', '')}"
                    )
                except Exception as me:
                    logger.warning(f"⚠️ Не удалось вычислить метрики для compatibility: {me}")
                return result
            else:
                return "🤝 Анализ совместимости завершён. Получены рекомендации по партнёрству."
        except Exception as e:
            logger.error(f"❌ Ошибка анализа совместимости: {e}")
            raise Exception(f"Ошибка анализа совместимости: {e}")

    async def generate_daily_forecast(self, company_data: Dict[str, Any], daily_astrology: str = "", today_news: str = "") -> str:
        """
        Генерация ежедневного прогноза для компании.

        Args:
            company_data (Dict): Данные компании
            daily_astrology (str): Астрологические влияния текущего дня
            today_news (str): Краткая сводка актуальных новостей на сегодня

        Returns:
            str: Сгенерированный ежедневный прогноз
        """
        try:
            # Определяем знаки зодиака (компании, владельца, директора)
            company_zodiac = self._get_zodiac_safe(company_data.get('registration_date'))
            owner_zodiac = self._get_zodiac_safe(company_data.get('owner_birth_date'))
            director_zodiac = self._get_zodiac_safe(company_data.get('director_birth_date'))

            # Подготавливаем данные для генерации прогноза
            chart_data = {
                "company_data": company_data,
                "company_zodiac": company_zodiac,
                "owner_zodiac": owner_zodiac,
                "director_zodiac": director_zodiac,
                "daily_astrology": daily_astrology,
                "today_news": today_news[:1500] if today_news else ""
            }

            if not self.openai_client:
                raise Exception("OpenAI клиент не инициализирован")

            result = self.openai_client.generate_astro_analysis(chart_data, "daily_forecast")
            logger.info(f"📅 Ежедневный прогноз для компании \"{company_data.get('name', '')}\" выполнен")

            if result:
                try:
                    profile = load_scoring_profile("daily_forecast")
                    local_score = compute_score(result, profile)
                    critic_feedback = self.openai_client.criticize_answer("daily_forecast", result, profile)
                    logger.info(
                        f"📅 Локальная оценка: {local_score['score']}/10 — "
                        f"Оценка критика: {critic_feedback.get('score', 'N/A')}/10, "
                        f"Комментарий критика: {critic_feedback.get('comment', '')}"
                    )
                except Exception as me:
                    logger.warning(f"⚠️ Не удалось вычислить метрики для daily_forecast: {me}")
                return result
            else:
                return "📅 Ежедневный прогноз готов. Получены рекомендации на сегодняшний день."
        except Exception as e:
            logger.error(f"❌ Ошибка генерации ежедневного прогноза: {e}")
            raise Exception(f"Ошибка генерации ежедневного прогноза: {e}")

    def _get_zodiac_safe(self, date_value: Any) -> str:
        """
        Безопасное определение знака зодиака по значению даты.

        Args:
            date_value (Any): Дата (datetime или строка)

        Returns:
            str: Название знака зодиака или "Неизвестно"
        """
        try:
            if not date_value:
                return "Неизвестно"
            if isinstance(date_value, str):
                # Парсим строковую дату в datetime, если возможно
                for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S'):
                    try:
                        date_value = datetime.strptime(date_value, fmt)
                        break
                    except ValueError:
                        continue
                if isinstance(date_value, str):
                    return "Неизвестно"
            # Теперь date_value гарантированно datetime
            return get_zodiac_sign(date_value) or "Неизвестно"
        except Exception:
            return "Неизвестно"
