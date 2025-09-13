# -*- coding: utf-8 -*-
"""
OpenAI API клиент для астрологических вычислений
Замена Gemini согласно требованиям пользователя
"""

import os
from typing import Dict, Any, Optional, Union
from datetime import datetime
from pytz import UTC
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False

from utils.config import load_config
from utils.logger import setup_logger

# Импортируем промпты для генерации и критики
from ai_astrologist.prompts import (
    ASTRO_RABBIT_SYSTEM_PROMPT,
    COMPANY_ZODIAC_INFO_PROMPT,
    BUSINESS_FORECAST_PROMPT,
    COMPATIBILITY_PROMPT,
    DAILY_FORECAST_PROMPT,
    CRITIC_PROMPT
)

logger = setup_logger()

class OpenAIAstroClient:
    """Клиент для работы с OpenAI API"""
    def __init__(self):
        """Инициализация OpenAI клиента"""
        self.config = load_config()
        self.client: Optional[Any] = None
        try:
            if not OPENAI_AVAILABLE or not openai:
                raise ImportError("OpenAI SDK не установлен")
            # Настраиваем OpenAI API клиента
            self.client = openai.OpenAI(api_key=self.config.openai.api_key)
            logger.info("🔮 OpenAI астрологический клиент инициализирован")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации OpenAI: {e}")
            self.client = None

    def get_birth_chart(self, birth_date: datetime, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Создание натальной карты через OpenAI

        Args:
            birth_date (datetime): Дата регистрации/рождения
            latitude (float): Широта места
            longitude (float): Долгота места

        Returns:
            Dict[str, Any]: Данные натальной карты (JSON-поля)
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
        """Базовая натальная карта при недоступности OpenAI API"""
        from utils.helpers import get_zodiac_sign
        sun_sign = get_zodiac_sign(birth_date.month, birth_date.day)
        return {
            "sun_sign": sun_sign,
            "moon_sign": sun_sign,  # Упрощение – при отсутствии API берём знак солнца для всех полей
            "rising_sign": sun_sign,
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
        Генерация общего гороскопа через OpenAI

        Args:
            prompt (str): Промпт для генерации
            max_tokens (int): Максимальное количество токенов

        Returns:
            str: Сгенерированный гороскоп (или сообщение об ошибке)
        """
        if not OPENAI_AVAILABLE or not self.config.openai.api_key or not self.client:
            logger.warning("⚠️ OpenAI недоступен")
            return "⚠️ Сервис временно недоступен. Попробуйте позже."
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ты профессиональный астролог AstroRabbit. Создаёшь качественные астрологические прогнозы на русском языке."},
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

    async def analyze_compatibility(self, person1_data: Dict[str, Any], person2_data: Dict[str, Any]) -> str:
        """
        Анализ совместимости двух людей через OpenAI

        Args:
            person1_data (Dict): Данные первого человека (включая sun_sign)
            person2_data (Dict): Данные второго человека (включая sun_sign)

        Returns:
            str: Анализ совместимости (или сообщение об ошибке)
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
                    {"role": "system", "content": "Ты эксперт по астрологической совместимости. Даёшь точные и полезные анализы отношений."},
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
        Генерация астрологического анализа через OpenAI (согласно профилю анализа).

        Args:
            chart_data (Dict): Входные данные (данные компании/объекта, новости, предварительные расчёты)
            analysis_type (str): Тип анализа (например, "zodiac_info", "business_forecast", "compatibility", "daily_forecast")

        Returns:
            str: Сгенерированный текст анализа (или сообщение об ошибке)
        """
        if not OPENAI_AVAILABLE or not self.config.openai.api_key or not self.client:
            return "Астрологический анализ недоступен (OpenAI API не настроен)"
        try:
            # Вспомогательная функция безопасного форматирования даты
            def safe_date(value: Any) -> str:
                if not value:
                    return "Не указано"
                if isinstance(value, datetime):
                    return value.strftime('%d.%m.%Y')
                try:
                    dt = datetime.fromisoformat(str(value))
                    return dt.strftime('%d.%m.%Y')
                except Exception:
                    return str(value)

            # Формируем system- и user-промпты на основе типа анализа
            system_msg = {"role": "system", "content": ASTRO_RABBIT_SYSTEM_PROMPT.strip()}
            user_msg = {"role": "user", "content": ""}

            if analysis_type in ["zodiac", "zodiac_info"]:
                data = chart_data
                comp = data.get("company_data", {})
                prompt_text = COMPANY_ZODIAC_INFO_PROMPT.format(
                    company_name=comp.get('name', ''),
                    registration_date=safe_date(comp.get('registration_date')),
                    registration_place=comp.get('registration_place', ''),
                    zodiac_sign=data.get('zodiac_sign', '')
                )
                # Добавляем подробную астрологическую информацию (если есть)
                if data.get('astro_info'):
                    prompt_text += data['astro_info']
                # Если в шаблоне предусмотрена вставка новостей, заменим её
                if "{news_data}" in prompt_text:
                    prompt_text = prompt_text.replace("{news_data}", str(data.get('news_data', '')))
                user_msg['content'] = prompt_text

            elif analysis_type in ["business_forecast", "business", "forecast"]:
                data = chart_data
                comp = data.get("company_data", {})
                prompt_text = BUSINESS_FORECAST_PROMPT.format(
                    company_name=comp.get('name', ''),
                    registration_date=safe_date(comp.get('registration_date')),
                    registration_place=comp.get('registration_place', ''),
                    business_sphere=comp.get('business_sphere', ''),
                    company_zodiac=data.get('company_zodiac', ''),
                    owner_name=comp.get('owner_name', 'Не указано'),
                    owner_birth_date=safe_date(comp.get('owner_birth_date')),
                    owner_zodiac=data.get('owner_zodiac', ''),
                    owner_numerology=data.get('owner_numerology', 0),
                    director_name=comp.get('director_name', 'Не указано'),
                    director_birth_date=safe_date(comp.get('director_birth_date')),
                    director_zodiac=data.get('director_zodiac', ''),
                    director_numerology=data.get('director_numerology', 0),
                    astrology_data=str(data.get('astrology_data', ''))[:1500],
                    news_data=str(data.get('news_data', ''))[:1500]
                )
                user_msg['content'] = prompt_text

            elif analysis_type == "compatibility":
                data = chart_data
                comp = data.get("company_data", {})
                obj = data.get("object_data", {})
                prompt_text = COMPATIBILITY_PROMPT.format(
                    company_name=comp.get('name', ''),
                    company_zodiac=data.get('company_zodiac', ''),
                    business_sphere=comp.get('business_sphere', ''),
                    object_type=data.get('object_type', ''),
                    object_name=obj.get('name', ''),
                    object_birth_date=safe_date(obj.get('birth_date')),
                    object_birth_place=obj.get('birth_place', ''),
                    object_zodiac=data.get('object_zodiac', ''),
                    object_numerology=data.get('object_numerology', 0)
                )
                user_msg['content'] = prompt_text

            elif analysis_type in ["daily_forecast", "daily"]:
                data = chart_data
                comp = data.get("company_data", {})
                prompt_text = DAILY_FORECAST_PROMPT.format(
                    company_name=comp.get('name', ''),
                    company_zodiac=data.get('company_zodiac', ''),
                    business_sphere=comp.get('business_sphere', ''),
                    owner_zodiac=data.get('owner_zodiac', ''),
                    director_zodiac=data.get('director_zodiac', ''),
                    daily_astrology=str(data.get('daily_astrology', ''))[:1000],
                    today_news=str(data.get('today_news', ''))[:1500]
                )
                user_msg['content'] = prompt_text

            else:
                # Общий случай для неизвестного типа анализа
                base_prompt = "Сделай астрологический анализ"
                prompt_text = f"{base_prompt} на основе следующих данных:\n{json.dumps(chart_data, ensure_ascii=False, indent=2)}"
                user_msg['content'] = prompt_text

            # Отправляем сообщения системе и пользователю в OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[system_msg, user_msg],
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

    def criticize_answer(self, profile_name: str, answer_text: str, scoring_profile: Dict[str, Any]) -> Dict[str, Union[float, str]]:
        """
        Запрос к модели-критику для оценки ответа ассистента и получения комментария.

        Args:
            profile_name (str): Название профиля (типа анализа), для контекста критика
            answer_text (str): Полный ответ ассистента (включая SELF-SCORE в конце)
            scoring_profile (Dict): Профиль метрик (непосредственно не используется при формировании запроса)

        Returns:
            Dict: {'score': итоговая оценка (float или None), 'comment': комментарий (str)}
        """
        if not OPENAI_AVAILABLE or not self.config.openai.api_key or not self.client:
            return {"score": None, "comment": "API недоступен"}
        try:
            # Выделяем часть самооценки ассистента (SELF-SCORE), если она есть
            self_score_part = "не указан"
            main_answer = answer_text
            if "SELF-SCORE:" in answer_text:
                idx = answer_text.find("SELF-SCORE:")
                main_answer = answer_text[:idx].strip()
                self_score_part = answer_text[idx:].strip()
            # Формируем ввод для критика согласно шаблону CRITIC_PROMPT
            critic_input = (f"1) исходный запрос/тип опции: {profile_name}\n"
                            f"2) полный ответ ассистента:\n{main_answer}\n"
                            f"3) конфиг критериев: (профиль '{profile_name}')\n"
                            f"4) Self-score ассистента: {self_score_part}")
            critic_prompt = CRITIC_PROMPT + "\n" + critic_input
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": critic_prompt}],
                temperature=0.0,
                max_tokens=500
            )
            critique = response.choices[0].message.content.strip()
            # Парсим оценку и комментарий из ответа критика
            critic_score = None
            critic_comment = ""
            for line in critique.splitlines():
                line = line.strip()
                if line.upper().startswith("TARGET-SCORE"):
                    # Ожидаемый формат: "TARGET-SCORE: X.Y/10"
                    try:
                        critic_score = float(line.split(":", 1)[1].split("/")[0].strip())
                    except Exception:
                        critic_score = None
                if line.upper().startswith("КОММЕНТАР") or line.upper().startswith("COMMENT"):
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        critic_comment = parts[1].strip()
            return {"score": critic_score, "comment": critic_comment}
        except Exception as e:
            logger.error(f"❌ Ошибка оценки критиком: {e}")
            return {"score": None, "comment": f"Ошибка критика: {e}"}

    def get_model_info(self) -> Dict[str, Any]:
        """Информация о подключенной модели OpenAI"""
        return {
            "provider": "OpenAI",
            "model": "gpt-4",
            "available": OPENAI_AVAILABLE and bool(self.client),
            "features": ["text_generation", "json_mode", "function_calling"]
        }
