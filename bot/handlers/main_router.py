# -*- coding: utf-8 -*-
"""
Главный роутер для координации всех обработчиков бота
"""

from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes

from .base_handler import BaseHandler
from .company_handler import CompanyHandler
from .forecast_handler import ForecastHandler
from .zodiac_handler import ZodiacHandler
from .compatibility_handler import CompatibilityHandler
from .daily_handler import DailyHandler
from ..states import BotState
from ..keyboards import BotKeyboards
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from utils.logger import setup_logger
from utils.performance import rate_limit, monitor_performance

logger = setup_logger()


class MainRouter(BaseHandler):
    """Главный роутер для координации всех обработчиков"""
    
    def __init__(self):
        """Инициализация главного роутера"""
        super().__init__()
        
        # Инициализируем специализированные обработчики
        self.company_handler = CompanyHandler()
        self.forecast_handler = ForecastHandler()
        self.zodiac_handler = ZodiacHandler()
        self.compatibility_handler = CompatibilityHandler()
        self.daily_handler = DailyHandler()
        
        # Инициализируем клавиатуры
        self.keyboards = BotKeyboards()
    
    # Основные команды бота
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        if not update.effective_user:
            return
            
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "Пользователь"
        
        try:
            # Сбрасываем состояние пользователя
            self.state_manager.set_user_state(user_id, BotState.MAIN_MENU)
            
            # Приветственное сообщение
            welcome_text = (
                f"🌟 <b>Добро пожаловать, {user_name}!</b>\n\n"
                "Я — Astro_Rabbit, ваш персональный астролог для бизнеса.\n\n"
                "🔮 <b>Что я умею:</b>\n"
                "• Анализировать знаки зодиака компаний\n"
                "• Составлять бизнес-прогнозы\n"
                "• Проверять совместимость с партнерами\n"
                "• Давать ежедневные рекомендации\n\n"
                "Выберите действие:"
            )
            
            if update.message:
                await update.message.reply_text(
                    welcome_text,
                    parse_mode='HTML',
                    reply_markup=self.keyboards.get_main_menu_keyboard()
                )
            else:
                await update.callback_query.edit_message_text(
                    welcome_text,
                    parse_mode='HTML',
                    reply_markup=self.keyboards.get_main_menu_keyboard()
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка команды /start: {e}")
            if update.message:
                await update.message.reply_text(
                    f"❌ Произошла ошибка: {str(e)}",
                    reply_markup=self.keyboards.get_main_menu_keyboard()
                )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        if not update.effective_user:
            return
            
        help_text = (
            "📖 <b>СПРАВКА ПО БОТУ</b>\n\n"
            "🔮 <b>Основные функции:</b>\n"
            "• <b>Мои компании</b> — управление профилями компаний\n"
            "• <b>Знак зодиака</b> — астрологический анализ компании\n"
            "• <b>Бизнес-прогноз</b> — полный прогноз с рекомендациями\n"
            "• <b>Совместимость</b> — анализ совместимости с партнерами\n"
            "• <b>Ежедневные прогнозы</b> — утренние рекомендации\n\n"
            "💡 <b>Как начать:</b>\n"
            "1. Добавьте компанию в разделе «Мои компании»\n"
            "2. Сделайте её активной\n"
            "3. Получайте персональные прогнозы!\n\n"
            "❓ <b>Нужна помощь?</b>\n"
            "Обратитесь к администратору @admin"
        )
        
        try:
            if update.message:
                await update.message.reply_text(
                    help_text,
                    parse_mode='HTML',
                    reply_markup=self.keyboards.get_back_inline_button()
                )
            else:
                await update.callback_query.edit_message_text(
                    help_text,
                    parse_mode='HTML',
                    reply_markup=self.keyboards.get_back_inline_button()
                )
        except Exception as e:
            logger.error(f"❌ Ошибка команды /help: {e}")
    
    async def companies_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /companies"""
        await self.company_handler.show_companies_menu(update, context)
    
    async def zodiac_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /zodiac"""
        if not update.effective_user:
            return
            
        user_id = update.effective_user.id
        
        # Проверяем наличие активной компании
        user_data = self.state_manager.get_user_data(user_id)
        active_company_id = user_data.get('active_company_id')
        
        if not active_company_id:
            await self._show_no_active_company_message(update)
            return
        
        # Получаем данные компании и переходим к анализу
        company_data = await self._get_company_data(user_id, active_company_id)
        if not company_data:
            await self._show_no_active_company_message(update)
            return
        
        # Вызываем обработчик знаков зодиака
        await self.zodiac_handler.show_zodiac_menu(update, context)
    
    @rate_limit()
    @monitor_performance("forecast_command")
    async def forecast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /forecast"""
        if not update.effective_user:
            return
            
        user_id = update.effective_user.id
        
        # Проверяем наличие активной компании
        user_data = self.state_manager.get_user_data(user_id)
        active_company_id = user_data.get('active_company_id')
        
        if not active_company_id:
            await self._show_no_active_company_message(update)
            return
        
        # Получаем данные компании и переходим к прогнозу
        company_data = await self._get_company_data(user_id, active_company_id)
        if not company_data:
            await self._show_no_active_company_message(update)
            return
        
        # Сохраняем данные компании для обработчика
        context.user_data['selected_company'] = company_data
        
        # Вызываем обработчик прогноза
        await self.forecast_handler.handle_company_business_forecast(update, context)
    
    async def compatibility_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /compatibility"""
        await self.compatibility_handler.show_compatibility_menu(update, context)
    
    async def daily_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /daily"""
        await self.daily_handler.show_daily_menu(update, context)
    
    async def cabinet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /cabinet"""
        await self._show_coming_soon_message(update, "Личный кабинет")
    
    async def tariffs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /tariffs"""
        await self._show_coming_soon_message(update, "Тарифы")
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /settings"""
        await self._show_coming_soon_message(update, "Настройки")
    
    # Обработчик сообщений
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        if not update.effective_user or not update.message:
            return
            
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        try:
            # Получаем текущее состояние пользователя
            user_state = self.state_manager.get_user_state(user_id)
            
            # Роутинг по состояниям
            if user_state == BotState.COMPANY_NAME_INPUT:
                await self.company_handler.handle_company_name_input(update, context, text)
            elif user_state == BotState.COMPANY_REG_DATE_INPUT:
                await self.company_handler.handle_registration_date_input(update, context, text)
            elif user_state == BotState.COMPANY_REG_PLACE_INPUT:
                await self.company_handler.handle_registration_place_input(update, context, text)
            elif user_state == BotState.COMPANY_OWNER_NAME_INPUT:
                await self.company_handler.handle_owner_name_input(update, context, text)
            elif user_state == BotState.COMPANY_OWNER_BIRTH_INPUT:
                await self.company_handler.handle_owner_birth_input(update, context, text)
            elif user_state == BotState.COMPANY_DIRECTOR_NAME_INPUT:
                await self.company_handler.handle_director_name_input(update, context, text)
            elif user_state == BotState.COMPANY_DIRECTOR_BIRTH_INPUT:
                await self.company_handler.handle_director_birth_input(update, context, text)
            elif user_state == BotState.MAIN_MENU:
                await self._handle_main_menu(update, context, text)
            else:
                # Проверяем состояния новых обработчиков
                user_id = update.effective_user.id
                
                # Проверяем состояния CompatibilityHandler
                compatibility_state = self.compatibility_handler.get_user_state(user_id)
                if compatibility_state:
                    if compatibility_state.get('step') == 'waiting_for_first_object':
                        await self.compatibility_handler.handle_first_object_input(update, context)
                    elif compatibility_state.get('step') == 'waiting_for_second_object':
                        await self.compatibility_handler.handle_second_object_input(update, context)
                    return
                
                # Проверяем состояния DailyHandler
                daily_state = self.daily_handler.get_user_state(user_id)
                if daily_state:
                    if daily_state.get('step') == 'waiting_for_company':
                        await self.daily_handler.handle_company_input(update, context)
                    return
                
                # Проверяем состояния CompanyHandler
                company_state = self.state_manager.get_user_state(user_id)
                if company_state:
                    if company_state == BotState.COMPANY_NAME_INPUT:
                        await self.company_handler.handle_company_name_input(update, context, text)
                    elif company_state == BotState.COMPANY_REG_DATE_INPUT:
                        await self.company_handler.handle_registration_date_input(update, context, text)
                    elif company_state == BotState.COMPANY_REG_CITY_INPUT:
                        await self.company_handler.handle_registration_city_input(update, context, text)
                    elif company_state == BotState.COMPANY_OWNER_NAME_INPUT:
                        await self.company_handler.handle_owner_name_input(update, context, text)
                    elif company_state == BotState.COMPANY_OWNER_BIRTH_INPUT:
                        await self.company_handler.handle_owner_birth_input(update, context, text)
                    elif company_state == BotState.COMPANY_DIRECTOR_NAME_INPUT:
                        await self.company_handler.handle_director_name_input(update, context, text)
                    elif company_state == BotState.COMPANY_DIRECTOR_BIRTH_INPUT:
                        await self.company_handler.handle_director_birth_input(update, context, text)
                    return
                
                await self._handle_unknown_state(update, context, text)
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения: {e}")
            await update.message.reply_text(
                f"❌ Произошла ошибка: {str(e)}",
                reply_markup=self.keyboards.get_main_menu_keyboard()
            )
    
    # Обработчик callback запросов
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback запросов"""
        if not update.callback_query or not update.effective_user:
            return
            
        query = update.callback_query
        callback_data = query.data
        
        try:
            # Роутинг callback запросов
            if callback_data == "companies" or callback_data == "companies_menu":
                await self.company_handler.show_companies_menu(update, context)
            elif callback_data == "add_company":
                await self.company_handler.start_add_company(update, context)
            elif callback_data.startswith("select_company_"):
                company_id = callback_data.replace("select_company_", "")
                await self.company_handler.select_company(update, context, company_id)
            elif callback_data.startswith("set_active_company_"):
                company_id = callback_data.replace("set_active_company_", "")
                await self.company_handler.set_active_company(update, context, company_id)
            elif callback_data.startswith("delete_company_"):
                company_id = callback_data.replace("delete_company_", "")
                await self.company_handler.delete_company(update, context, company_id)
            elif callback_data.startswith("analyze_company_"):
                company_id = callback_data.replace("analyze_company_", "")
                await self.company_handler.analyze_company(update, context, company_id)
            elif callback_data.startswith("sphere_"):
                await self.company_handler.handle_sphere_selection(update, context, callback_data)
            elif callback_data.startswith("forecast_"):
                await self._handle_forecast_callback(update, context, callback_data)
            elif callback_data == "zodiac_menu":
                await self.zodiac_handler.show_zodiac_menu(update, context)
            elif callback_data.startswith("zodiac_analysis_"):
                await self.zodiac_handler.analyze_zodiac_sign(update, context)
            elif callback_data.startswith("compatibility_"):
                await self.compatibility_handler.start_compatibility_analysis(update, context)
            elif callback_data == "compatibility_menu":
                await self.compatibility_handler.show_compatibility_menu(update, context)
            elif callback_data == "daily_menu":
                await self.daily_handler.show_daily_menu(update, context)
            elif callback_data.startswith("daily_"):
                await self.daily_handler.start_daily_forecast(update, context)
            elif callback_data == "back_to_main_menu" or callback_data == "main_menu":
                await self.start_command(update, context)
            elif callback_data == "zodiac":
                await self.zodiac_command(update, context)
            elif callback_data == "forecast":
                await self.forecast_command(update, context)
            elif callback_data == "compatibility":
                await self.compatibility_command(update, context)
            elif callback_data == "daily":
                await self.daily_command(update, context)
            elif callback_data == "settings":
                await self.settings_command(update, context)
            else:
                await self._handle_unknown_callback(update, context, callback_data)
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки callback: {e}")
            await query.edit_message_text(
                f"❌ Произошла ошибка: {str(e)}",
                reply_markup=self.keyboards.get_back_inline_button()
            )
    
    # Вспомогательные методы
    
    async def _handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Обработка сообщений в главном меню"""
        if not update.message:
            return
            
        # Простое текстовое меню
        if "компании" in text.lower():
            await self.companies_command(update, context)
        elif "прогноз" in text.lower():
            await self.forecast_command(update, context)
        elif "знак" in text.lower() or "зодиак" in text.lower():
            await self.zodiac_command(update, context)
        elif "совместимость" in text.lower():
            await self.compatibility_command(update, context)
        elif "помощь" in text.lower() or "help" in text.lower():
            await self.help_command(update, context)
        else:
            await update.message.reply_text(
                "🤔 Не понимаю команду. Используйте меню или команды:\n\n"
                "/companies - Мои компании\n"
                "/forecast - Бизнес-прогноз\n"
                "/zodiac - Знак зодиака\n"
                "/help - Справка",
                reply_markup=self.keyboards.get_main_menu_keyboard()
            )
    
    async def _handle_forecast_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Обработка callback запросов для прогнозов"""
        if callback_data == "forecast_quick":
            await self.forecast_handler.handle_quick_forecast(update, context)
        elif callback_data == "forecast_financial":
            await self.forecast_handler.handle_financial_forecast(update, context)
        elif callback_data == "forecast_partnership":
            await self.forecast_handler.handle_partnership_forecast(update, context)
        elif callback_data == "forecast_risk":
            await self.forecast_handler.handle_risk_forecast(update, context)
        else:
            await self._handle_unknown_callback(update, context, callback_data)
    
    async def _show_no_active_company_message(self, update: Update):
        """Показать сообщение об отсутствии активной компании"""
        message_text = (
            "❌ <b>НЕТ АКТИВНОЙ КОМПАНИИ</b>\n\n"
            "Для получения прогнозов сначала добавьте компанию и сделайте её активной.\n\n"
            "Перейдите в раздел «Мои компании»:"
        )
        
        if update.message:
            await update.message.reply_text(
                message_text,
                parse_mode='HTML',
                reply_markup=self.keyboards.get_main_menu_keyboard()
            )
        else:
            await update.callback_query.edit_message_text(
                message_text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏢 Мои компании", callback_data="companies_menu")],
                    [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main_menu")]
                ])
            )
    
    async def _show_coming_soon_message(self, update: Update, feature_name: str):
        """Показать сообщение о скором появлении функции"""
        message_text = f"🚧 <b>{feature_name.upper()}</b>\n\nФункция находится в разработке и скоро будет доступна!"
        
        if update.message:
            await update.message.reply_text(
                message_text,
                parse_mode='HTML',
                reply_markup=self.keyboards.get_back_inline_button()
            )
        else:
            await update.callback_query.edit_message_text(
                message_text,
                parse_mode='HTML',
                reply_markup=self.keyboards.get_back_inline_button()
            )
    
    async def _handle_unknown_state(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Обработка неизвестного состояния"""
        if not update.message:
            return
            
        await update.message.reply_text(
            "🤔 Не понимаю команду. Используйте главное меню:",
            reply_markup=self.keyboards.get_main_menu_keyboard()
        )
    
    async def _handle_unknown_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Обработка неизвестного callback"""
        if not update.callback_query:
            return
            
        logger.warning(f"⚠️ Неизвестный callback: {callback_data}")
        await update.callback_query.edit_message_text(
            "❓ Неизвестная команда. Возвращаемся в главное меню:",
            reply_markup=self.keyboards.get_main_menu_keyboard()
        )
    
    # Недостающие методы для совместимости
    async def contact_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик контактов"""
        if not update.message:
            return
        await update.message.reply_text("📞 Контакт получен, но функция пока не реализована")
    
    async def document_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик документов"""
        if not update.message:
            return
        await update.message.reply_text("📄 Документ получен, но функция пока не реализована")
