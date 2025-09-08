# -*- coding: utf-8 -*-
"""
Временная прокладка для обратной совместимости.
Все промты вынесены в ai_astrologist/prompts/*.py
РЕКОМЕНДАЦИЯ: постепенно переводить импорты на точечные файлы.
"""

from ai_astrologist.prompts.system import ASTRO_RABBIT_SYSTEM_PROMPT
from ai_astrologist.prompts.companies import COMPANIES_PROMPT
from ai_astrologist.prompts.zodiac_info import COMPANY_ZODIAC_INFO_PROMPT
from ai_astrologist.prompts.business_forecast import BUSINESS_FORECAST_PROMPT
from ai_astrologist.prompts.compatibility import COMPATIBILITY_PROMPT
from ai_astrologist.prompts.daily_forecast import DAILY_FORECAST_PROMPT
from ai_astrologist.prompts.critic_prompt import CRITIC_PROMPT

__all__ = [
    "ASTRO_RABBIT_SYSTEM_PROMPT",
    "COMPANIES_PROMPT",
    "COMPANY_ZODIAC_INFO_PROMPT",
    "BUSINESS_FORECAST_PROMPT",
    "COMPATIBILITY_PROMPT",
    "DAILY_FORECAST_PROMPT",
    "CRITIC_PROMPT",
]
