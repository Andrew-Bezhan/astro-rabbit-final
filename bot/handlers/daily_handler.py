# -*- coding: utf-8 -*-
"""
Обработчик для ежедневных прогнозов
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from .base_handler import BaseHandler
from utils.logger import setup_logger
from ai_astrologist.prompts import DAILY_FORECAST_PROMPT
from datetime import datetime, timedelta
import json

logger = setup_logger()


class DailyHandler(BaseHandler):
    """Обработчик для ежедневных прогнозов"""
    
    def __init__(self):
        super().__init__()
        self.user_states = {}  # Хранение состояний пользователей
    
    async def show_daily_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню ежедневных прогнозов"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        
        # Получаем текущую дату
        today = datetime.now()
        
        keyboard = [
            [InlineKeyboardButton("📅 Прогноз на сегодня", callback_data="daily_today")],
            [InlineKeyboardButton("📅 Прогноз на завтра", callback_data="daily_tomorrow")],
            [InlineKeyboardButton("📅 Прогноз на неделю", callback_data="daily_week")],
            [InlineKeyboardButton("📅 Прогноз на месяц", callback_data="daily_month")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"📅 **Ежедневные прогнозы**\n\n"
            f"Текущая дата: {today.strftime('%d.%m.%Y')}\n\n"
            f"Выберите период для прогноза:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def start_daily_forecast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать ежедневный прогноз"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        callback_data = update.callback_query.data
        
        # Определяем тип прогноза
        forecast_type = callback_data.replace("daily_", "")
        
        # Сохраняем тип прогноза для пользователя
        self.user_states[user_id] = {
            'forecast_type': forecast_type,
            'step': 'waiting_for_company'
        }
        
        # Получаем инструкции для ввода данных
        instructions = self._get_instructions_for_type(forecast_type)
        
        await update.callback_query.edit_message_text(
            f"📅 **{instructions['title']}**\n\n"
            f"{instructions['description']}\n\n"
            f"📝 Введите название компании для прогноза:",
            parse_mode='Markdown'
        )
    
    async def handle_company_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода компании"""
        if not update.effective_user or not update.message:
            return
            
        user_id = update.effective_user.id
        
        if user_id not in self.user_states:
            return
            
        state = self.user_states[user_id]
        
        if state['step'] != 'waiting_for_company':
            return
        
        # Сохраняем компанию
        company_name = update.message.text.strip()
        state['company_name'] = company_name
        state['step'] = 'generating'
        
        # Удаляем состояние пользователя
        del self.user_states[user_id]
        
        # Запускаем генерацию прогноза
        await self._perform_daily_forecast(update, context, state)
    
    async def _perform_daily_forecast(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
        """Выполнить ежедневный прогноз"""
        user_id = update.effective_user.id
        
        try:
            # Получаем актуальные новости
            news_data = await self._get_news_data()
            
            # Получаем астрологические данные
            astro_data = await self._get_daily_astrology()
            
            # Определяем даты для прогноза
            dates_info = self._get_dates_for_forecast(state['forecast_type'])
            
            # Формируем промпт для анализа
            prompt = DAILY_FORECAST_PROMPT.format(
                company_name=state['company_name'],
                forecast_period=dates_info['period'],
                forecast_dates=dates_info['dates'],
                news_context=news_data,
                astrological_context=astro_data
            )
            
            # Отправляем сообщение о начале анализа
            await update.message.reply_text(
                f"📅 Генерирую {dates_info['period']} прогноз...\n\n"
                f"🏢 **{state['company_name']}**\n"
                f"📅 Период: {dates_info['dates']}\n"
                f"📰 Учитываю актуальные новости и астрологические данные",
                parse_mode='Markdown'
            )
            
            # Генерируем прогноз через AI
            forecast = await self.astro_agent.generate_analysis(
                prompt=prompt,
                user_id=user_id,
                analysis_type="daily_forecast"
            )
            
            if forecast and forecast.get('content'):
                # Валидируем результат
                validation_result = await self._validate_analysis(forecast['content'], "daily_forecast")
                
                # Формируем финальное сообщение
                message = f"📅 **{dates_info['period']} прогноз**\n\n"
                message += f"🏢 **{state['company_name']}**\n"
                message += f"📅 Период: {dates_info['dates']}\n\n"
                message += forecast['content']
                
                if validation_result['score'] < 7:
                    message += f"\n\n⚠️ *Качество прогноза: {validation_result['score']}/10*"
                
                # Добавляем кнопки
                keyboard = [
                    [InlineKeyboardButton("🔄 Новый прогноз", callback_data=f"daily_{state['forecast_type']}")],
                    [InlineKeyboardButton("🔙 К прогнозам", callback_data="daily_menu")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Разбиваем длинное сообщение на части
                await self._send_long_message(
                    update.message, 
                    message, 
                    reply_markup=reply_markup
                )
                
                # Автосохранение
                await self._auto_save_analysis(user_id, forecast, "daily_forecast", f"{state['company_name']}_{dates_info['period']}")
                
            else:
                await update.message.reply_text(
                    "❌ Не удалось сгенерировать прогноз.\n"
                    "Попробуйте еще раз.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"daily_{state['forecast_type']}")
                    ]])
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка генерации прогноза: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при генерации прогноза.\n"
                "Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 К прогнозам", callback_data="daily_menu")
                ]])
            )
    
    def _get_instructions_for_type(self, forecast_type: str) -> dict:
        """Получить инструкции для типа прогноза"""
        instructions_map = {
            'today': {
                'title': 'Прогноз на сегодня',
                'description': 'Астрологический прогноз для компании на текущий день'
            },
            'tomorrow': {
                'title': 'Прогноз на завтра',
                'description': 'Астрологический прогноз для компании на завтрашний день'
            },
            'week': {
                'title': 'Прогноз на неделю',
                'description': 'Астрологический прогноз для компании на ближайшую неделю'
            },
            'month': {
                'title': 'Прогноз на месяц',
                'description': 'Астрологический прогноз для компании на текущий месяц'
            }
        }
        return instructions_map.get(forecast_type, instructions_map['today'])
    
    def _get_dates_for_forecast(self, forecast_type: str) -> dict:
        """Получить даты для прогноза"""
        today = datetime.now()
        
        if forecast_type == 'today':
            return {
                'period': 'Ежедневный',
                'dates': today.strftime('%d.%m.%Y')
            }
        elif forecast_type == 'tomorrow':
            tomorrow = today + timedelta(days=1)
            return {
                'period': 'На завтра',
                'dates': tomorrow.strftime('%d.%m.%Y')
            }
        elif forecast_type == 'week':
            week_end = today + timedelta(days=7)
            return {
                'period': 'Недельный',
                'dates': f"{today.strftime('%d.%m.%Y')} - {week_end.strftime('%d.%m.%Y')}"
            }
        elif forecast_type == 'month':
            month_end = today.replace(day=1) + timedelta(days=32)
            month_end = month_end.replace(day=1) - timedelta(days=1)
            return {
                'period': 'Месячный',
                'dates': f"{today.strftime('%d.%m.%Y')} - {month_end.strftime('%d.%m.%Y')}"
            }
        else:
            return {
                'period': 'Ежедневный',
                'dates': today.strftime('%d.%m.%Y')
            }
    
    def get_user_state(self, user_id: int) -> dict:
        """Получить состояние пользователя"""
        return self.user_states.get(user_id, {})
    
    def clear_user_state(self, user_id: int):
        """Очистить состояние пользователя"""
        if user_id in self.user_states:
            del self.user_states[user_id]
