# -*- coding: utf-8 -*-
"""
Клавиатуры для Telegram бота AstroRabbit
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class BotKeyboards:
    """Класс для создания клавиатур бота"""
    
    @staticmethod
    def get_main_menu_keyboard():
        """Получить главное меню"""
        return create_main_menu_keyboard()
    
    @staticmethod
    def get_back_inline_button():
        """Получить кнопку назад"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main_menu")]
        ])
    
    @staticmethod
    def get_company_actions_menu():
        """Получить меню действий с компанией"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 К действиям с компанией", callback_data="back_to_company_actions")]
        ])


def create_forecast_options_keyboard():
    """
    Создает инлайн-клавиатуру с дополнительными опциями для бизнес-прогноза
    """
    keyboard = [
        [
            InlineKeyboardButton("🚀 Быстрый прогноз на 3 месяца", callback_data="forecast_quick"),
            InlineKeyboardButton("💰 Прогноз финансов", callback_data="forecast_financial")
        ],
        [
            InlineKeyboardButton("🤝 Прогноз партнерства", callback_data="forecast_partnership"),
            InlineKeyboardButton("⚠️ Прогноз рисков", callback_data="forecast_risk")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_main_menu_keyboard():
    """
    Создает основное меню бота с кнопкой "Мои компании" поверх остальных
    """
    keyboard = [
        [
            InlineKeyboardButton("🏢 Мои компании", callback_data="companies")
        ],
        [
            InlineKeyboardButton("🌟 Знак зодиака", callback_data="zodiac"),
            InlineKeyboardButton("📊 Бизнес-прогноз", callback_data="forecast")
        ],
        [
            InlineKeyboardButton("🤝 Совместимость", callback_data="compatibility"),
            InlineKeyboardButton("📅 Ежедневный прогноз", callback_data="daily")
        ],
        [
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_company_management_keyboard():
    """
    Создает клавиатуру для управления компаниями
    """
    keyboard = [
        [
            InlineKeyboardButton("➕ Добавить компанию", callback_data="add_company"),
            InlineKeyboardButton("✏️ Редактировать", callback_data="edit_company")
        ],
        [
            InlineKeyboardButton("🗑️ Удалить компанию", callback_data="delete_company"),
            InlineKeyboardButton("✅ Выбрать активную", callback_data="select_active_company")
        ],
        [
            InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_back_to_menu_keyboard():
    """
    Создает простую клавиатуру с кнопкой "Назад в меню"
    """
    keyboard = [
        [
            InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)