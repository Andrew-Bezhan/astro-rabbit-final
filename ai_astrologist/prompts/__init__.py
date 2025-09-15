# -*- coding: utf-8 -*-
"""
Пакет промтов AstroRabbit.
Реэкспорт основных констант для удобного импорта:
from ai_astrologist.prompts import BUSINESS_FORECAST_PROMPT, ...
"""

from .system import ASTRO_RABBIT_SYSTEM_PROMPT
from .companies import COMPANIES_PROMPT
from .zodiac_info import COMPANY_ZODIAC_INFO_PROMPT
from .business_forecast import BUSINESS_FORECAST_PROMPT
from .compatibility import COMPATIBILITY_PROMPT
from .daily_forecast import DAILY_FORECAST_PROMPT
from .critic_prompt import CRITIC_PROMPT
from .quick_forecast import QUICK_FORECAST_PROMPT
from .financial_forecast import FINANCIAL_FORECAST_PROMPT
from .partnership_forecast import PARTNERSHIP_FORECAST_PROMPT
from .risk_forecast import RISK_FORECAST_PROMPT

__all__ = [
    "ASTRO_RABBIT_SYSTEM_PROMPT",
    "COMPANIES_PROMPT",
    "COMPANY_ZODIAC_INFO_PROMPT",
    "BUSINESS_FORECAST_PROMPT",
    "COMPATIBILITY_PROMPT",
    "DAILY_FORECAST_PROMPT",
    "CRITIC_PROMPT",
    "QUICK_FORECAST_PROMPT",
    "FINANCIAL_FORECAST_PROMPT",
    "PARTNERSHIP_FORECAST_PROMPT",
    "RISK_FORECAST_PROMPT",
]
