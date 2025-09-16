# -*- coding: utf-8 -*-
"""
Обработчик для бизнес-прогнозов
"""

from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from .base_handler import BaseHandler
from ..keyboards import create_forecast_options_keyboard
from ai_astrologist.prompts import (
    BUSINESS_FORECAST_PROMPT,
    QUICK_FORECAST_PROMPT, 
    FINANCIAL_FORECAST_PROMPT, 
    PARTNERSHIP_FORECAST_PROMPT, 
    RISK_FORECAST_PROMPT
)
from utils.logger import setup_logger

logger = setup_logger()


class ForecastHandler(BaseHandler):
    """Обработчик для бизнес-прогнозов"""
    
    async def handle_company_business_forecast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка бизнес-прогноза компании"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        query = update.callback_query
        
        try:
            # Получаем данные компании из context.user_data (сохраненные при выборе)
            company_data = None
            if context.user_data and 'selected_company' in context.user_data:
                company_data = context.user_data['selected_company']
            
            if not company_data:
                await query.edit_message_text(
                    "❌ Данные компании не найдены. Выберите компанию заново.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 К действиям с компанией", callback_data="back_to_company_actions")]
                    ])
                )
                return
            
            # Показываем сообщение о начале анализа
            await query.edit_message_text(
                "📈 Составляю бизнес-прогноз компании...\n⏳ Это может занять несколько секунд.",
                parse_mode=None
            )
            
            # Получаем новости для компании
            news_data = ""
            try:
                if self.news_analyzer and company_data and company_data.get('business_sphere'):
                    news_analysis = await self.news_analyzer.analyze_news_for_company(
                        company_sphere=company_data.get('business_sphere', ''),
                        days_back=7
                    )
                    # Преобразуем результат анализа в строку
                    if isinstance(news_analysis, dict) and 'summary' in news_analysis:
                        news_data = str(news_analysis['summary'])
                    else:
                        news_data = str(news_analysis)
            except Exception as e:
                logger.warning(f"⚠️ Не удалось получить новости: {e}")
            
            # Выполняем прогноз
            try:
                forecast_result = await self.astro_agent.generate_business_forecast(
                    company_data=company_data,
                    astrology_data="",
                    news_data=news_data
                )
            except Exception as e:
                logger.error(f"❌ Критическая ошибка прогноза: {e}")
                await query.edit_message_text(
                    f"❌ Произошла ошибка при генерации бизнес-прогноза:\n\n{str(e)}\n\nПожалуйста, попробуйте позже или обратитесь к администратору.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 К действиям с компанией", callback_data="back_to_company_actions")]
                    ])
                )
                return
            
            # Валидируем и исправляем текст
            if self.validator:
                try:
                    forecast_result = await self.validator.validate_and_fix(
                        forecast_result, "forecast", BUSINESS_FORECAST_PROMPT
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка валидации: {e}. Используем результат без валидации.")
            
            # Очищаем HTML-теги
            forecast_result = self._clean_html_tags(forecast_result)
            
            # Автоматически сохраняем анализ
            await self._auto_save_analysis(user_id, company_data, "forecast", forecast_result)
            
            # Разбиваем длинный текст на части
            text_parts = self._split_long_text(forecast_result)
            
            if len(text_parts) == 1:
                # Короткий текст - отправляем как есть с кнопками дополнительных опций
                await query.edit_message_text(
                    f"<b>📈 БИЗНЕС-ПРОГНОЗ КОМПАНИИ</b>\n\n{forecast_result}",
                    parse_mode='HTML',
                    reply_markup=create_forecast_options_keyboard()
                )
            else:
                # Длинный текст - разбиваем на части
                # Проверяем, что context.user_data существует
                if context.user_data is not None:
                    context.user_data.update({
                        'analysis_parts': text_parts,
                        'total_parts': len(text_parts),
                        'current_part_index': 1,
                        'analysis_type': 'forecast',
                        'last_analysis_result': forecast_result,
                        'last_analysis_type': 'forecast'
                    })
                else:
                    logger.warning("⚠️ context.user_data is None, данные анализа не сохранены")
                
                # Показываем первую часть
                first_part = text_parts[0]
                keyboard = []
                
                if len(text_parts) > 1:
                    keyboard.append([InlineKeyboardButton("📄 Следующая часть", callback_data="next_part_2")])
                
                keyboard.append([InlineKeyboardButton("🔙 К действиям с компанией", callback_data="back_to_company_actions")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"<b>📈 БИЗНЕС-ПРОГНОЗ КОМПАНИИ</b>\n\n{first_part}\n\n📄 Показано 1 из {len(text_parts)} частей",
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка бизнес-прогноза компании: {e}")
            await query.edit_message_text(
                f"❌ Ошибка при составлении прогноза: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К действиям с компанией", callback_data="back_to_company_actions")]
                ])
            )
    
    async def handle_quick_forecast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик быстрого прогноза на 3 месяца"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        query = update.callback_query
        
        try:
            # Получаем данные активной компании
            user_data = self.state_manager.get_user_data(user_id)
            active_company_id = getattr(user_data, 'active_company_id', None)
            
            if not active_company_id:
                await query.edit_message_text(
                    "❌ Сначала выберите активную компанию.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 К прогнозу", callback_data="back_to_forecast")]
                    ])
                )
                return
            
            # Получаем данные компании из базы
            company_data = await self._get_company_data(user_id, active_company_id)
            if not company_data:
                await query.edit_message_text(
                    "❌ Данные компании не найдены.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 К прогнозу", callback_data="back_to_forecast")]
                    ])
                )
                return
            
            # Показываем индикатор загрузки
            await query.edit_message_text("🚀 Генерирую быстрый прогноз на 3 месяца...")
            
            # Получаем новости и астрологические данные
            news_data = await self._get_news_data()
            daily_astrology = await self._get_daily_astrology()
            
            # Генерируем прогноз
            forecast_result = await self.astro_agent.generate_forecast(
                prompt=QUICK_FORECAST_PROMPT,
                company_data=company_data,
                news_data=news_data,
                daily_astrology=daily_astrology
            )
            
            # Отправляем результат
            await query.edit_message_text(
                forecast_result,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К прогнозу", callback_data="back_to_forecast")]
                ])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации быстрого прогноза: {e}")
            await query.edit_message_text(
                f"❌ Ошибка генерации прогноза: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К прогнозу", callback_data="back_to_forecast")]
                ])
            )
    
    async def handle_financial_forecast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик прогноза финансов"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        query = update.callback_query
        
        try:
            # Получаем данные активной компании
            user_data = self.state_manager.get_user_data(user_id)
            active_company_id = getattr(user_data, 'active_company_id', None)
            
            if not active_company_id:
                await query.edit_message_text(
                    "❌ Сначала выберите активную компанию.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 К прогнозу", callback_data="back_to_forecast")]
                    ])
                )
                return
            
            # Получаем данные компании из базы
            company_data = await self._get_company_data(user_id, active_company_id)
            if not company_data:
                await query.edit_message_text(
                    "❌ Данные компании не найдены.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 К прогнозу", callback_data="back_to_forecast")]
                    ])
                )
                return
            
            # Показываем индикатор загрузки
            await query.edit_message_text("💰 Генерирую финансовый прогноз...")
            
            # Получаем новости и астрологические данные
            news_data = await self._get_news_data()
            daily_astrology = await self._get_daily_astrology()
            
            # Генерируем прогноз
            forecast_result = await self.astro_agent.generate_forecast(
                prompt=FINANCIAL_FORECAST_PROMPT,
                company_data=company_data,
                news_data=news_data,
                daily_astrology=daily_astrology
            )
            
            # Отправляем результат
            await query.edit_message_text(
                forecast_result,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К прогнозу", callback_data="back_to_forecast")]
                ])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации финансового прогноза: {e}")
            await query.edit_message_text(
                f"❌ Ошибка генерации прогноза: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К прогнозу", callback_data="back_to_forecast")]
                ])
            )
    
    async def handle_partnership_forecast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик прогноза партнерства"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        query = update.callback_query
        
        try:
            # Получаем данные активной компании
            user_data = self.state_manager.get_user_data(user_id)
            active_company_id = getattr(user_data, 'active_company_id', None)
            
            if not active_company_id:
                await query.edit_message_text(
                    "❌ Сначала выберите активную компанию.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 К прогнозу", callback_data="back_to_forecast")]
                    ])
                )
                return
            
            # Получаем данные компании из базы
            company_data = await self._get_company_data(user_id, active_company_id)
            if not company_data:
                await query.edit_message_text(
                    "❌ Данные компании не найдены.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 К прогнозу", callback_data="back_to_forecast")]
                    ])
                )
                return
            
            # Показываем индикатор загрузки
            await query.edit_message_text("🤝 Генерирую прогноз партнерства...")
            
            # Получаем новости и астрологические данные
            news_data = await self._get_news_data()
            daily_astrology = await self._get_daily_astrology()
            
            # Генерируем прогноз
            forecast_result = await self.astro_agent.generate_forecast(
                prompt=PARTNERSHIP_FORECAST_PROMPT,
                company_data=company_data,
                news_data=news_data,
                daily_astrology=daily_astrology
            )
            
            # Отправляем результат
            await query.edit_message_text(
                forecast_result,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К прогнозу", callback_data="back_to_forecast")]
                ])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации прогноза партнерства: {e}")
            await query.edit_message_text(
                f"❌ Ошибка генерации прогноза: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К прогнозу", callback_data="back_to_forecast")]
                ])
            )
    
    async def handle_risk_forecast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик прогноза рисков"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        query = update.callback_query
        
        try:
            # Получаем данные активной компании
            user_data = self.state_manager.get_user_data(user_id)
            active_company_id = getattr(user_data, 'active_company_id', None)
            
            if not active_company_id:
                await query.edit_message_text(
                    "❌ Сначала выберите активную компанию.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 К прогнозу", callback_data="back_to_forecast")]
                    ])
                )
                return
            
            # Получаем данные компании из базы
            company_data = await self._get_company_data(user_id, active_company_id)
            if not company_data:
                await query.edit_message_text(
                    "❌ Данные компании не найдены.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 К прогнозу", callback_data="back_to_forecast")]
                    ])
                )
                return
            
            # Показываем индикатор загрузки
            await query.edit_message_text("⚠️ Генерирую прогноз рисков...")
            
            # Получаем новости и астрологические данные
            news_data = await self._get_news_data()
            daily_astrology = await self._get_daily_astrology()
            
            # Генерируем прогноз
            forecast_result = await self.astro_agent.generate_forecast(
                prompt=RISK_FORECAST_PROMPT,
                company_data=company_data,
                news_data=news_data,
                daily_astrology=daily_astrology
            )
            
            # Отправляем результат
            await query.edit_message_text(
                forecast_result,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К прогнозу", callback_data="back_to_forecast")]
                ])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации прогноза рисков: {e}")
            await query.edit_message_text(
                f"❌ Ошибка генерации прогноза: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К прогнозу", callback_data="back_to_forecast")]
                ])
            )
