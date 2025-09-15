# -*- coding: utf-8 -*-
"""
Обработчик для анализа совместимости
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from .base_handler import BaseHandler
from utils.logger import setup_logger
from ai_astrologist.prompts import COMPATIBILITY_PROMPT
import json

logger = setup_logger()


class CompatibilityHandler(BaseHandler):
    """Обработчик для анализа совместимости"""
    
    def __init__(self):
        super().__init__()
        self.user_states = {}  # Хранение состояний пользователей
    
    async def show_compatibility_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню анализа совместимости"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        
        keyboard = [
            [InlineKeyboardButton("👥 Совместимость компаний", callback_data="compatibility_companies")],
            [InlineKeyboardButton("🤝 Совместимость с партнером", callback_data="compatibility_partner")],
            [InlineKeyboardButton("👤 Совместимость с сотрудником", callback_data="compatibility_employee")],
            [InlineKeyboardButton("🏢 Совместимость с контрагентом", callback_data="compatibility_counterparty")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "🤝 **Анализ совместимости**\n\n"
            "Выберите тип анализа совместимости:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def start_compatibility_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать анализ совместимости"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        callback_data = update.callback_query.data
        
        # Определяем тип анализа
        analysis_type = callback_data.replace("compatibility_", "")
        
        # Сохраняем тип анализа для пользователя
        self.user_states[user_id] = {
            'analysis_type': analysis_type,
            'step': 'waiting_for_first_object'
        }
        
        # Получаем инструкции для ввода данных
        instructions = self._get_instructions_for_type(analysis_type)
        
        await update.callback_query.edit_message_text(
            f"🤝 **Анализ совместимости: {instructions['title']}**\n\n"
            f"{instructions['description']}\n\n"
            f"📝 **Шаг 1 из 2:** {instructions['step1']}\n\n"
            f"Отправьте сообщение с названием:",
            parse_mode='Markdown'
        )
    
    async def handle_first_object_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода первого объекта"""
        if not update.effective_user or not update.message:
            return
            
        user_id = update.effective_user.id
        
        if user_id not in self.user_states:
            return
            
        state = self.user_states[user_id]
        
        if state['step'] != 'waiting_for_first_object':
            return
        
        # Сохраняем первый объект
        first_object = update.message.text.strip()
        state['first_object'] = first_object
        state['step'] = 'waiting_for_second_object'
        
        instructions = self._get_instructions_for_type(state['analysis_type'])
        
        await update.message.reply_text(
            f"✅ Первый объект сохранен: **{first_object}**\n\n"
            f"📝 **Шаг 2 из 2:** {instructions['step2']}\n\n"
            f"Отправьте сообщение с названием:",
            parse_mode='Markdown'
        )
    
    async def handle_second_object_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода второго объекта"""
        if not update.effective_user or not update.message:
            return
            
        user_id = update.effective_user.id
        
        if user_id not in self.user_states:
            return
            
        state = self.user_states[user_id]
        
        if state['step'] != 'waiting_for_second_object':
            return
        
        # Сохраняем второй объект
        second_object = update.message.text.strip()
        state['second_object'] = second_object
        state['step'] = 'analyzing'
        
        # Удаляем состояние пользователя
        del self.user_states[user_id]
        
        # Запускаем анализ
        await self._perform_compatibility_analysis(update, context, state)
    
    async def _perform_compatibility_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
        """Выполнить анализ совместимости"""
        user_id = update.effective_user.id
        
        try:
            # Получаем актуальные новости
            news_data = await self._get_news_data()
            
            # Формируем промпт для анализа
            prompt = COMPATIBILITY_PROMPT.format(
                object1_name=state['first_object'],
                object2_name=state['second_object'],
                object_status=state['analysis_type'],
                news_context=news_data
            )
            
            # Отправляем сообщение о начале анализа
            await update.message.reply_text(
                f"🤝 Анализирую совместимость...\n\n"
                f"📊 **{state['first_object']}** ↔️ **{state['second_object']}**\n"
                f"📰 Учитываю актуальные новости",
                parse_mode='Markdown'
            )
            
            # Генерируем анализ через AI
            analysis = await self.astro_agent.generate_analysis(
                prompt=prompt,
                user_id=user_id,
                analysis_type="compatibility_analysis"
            )
            
            if analysis and analysis.get('content'):
                # Валидируем результат
                validation_result = await self._validate_analysis(analysis['content'], "compatibility_analysis")
                
                # Формируем финальное сообщение
                message = f"🤝 **Анализ совместимости**\n\n"
                message += f"**{state['first_object']}** ↔️ **{state['second_object']}**\n\n"
                message += analysis['content']
                
                if validation_result['score'] < 7:
                    message += f"\n\n⚠️ *Качество анализа: {validation_result['score']}/10*"
                
                # Добавляем кнопки
                keyboard = [
                    [InlineKeyboardButton("🔄 Новый анализ", callback_data=f"compatibility_{state['analysis_type']}")],
                    [InlineKeyboardButton("🔙 К совместимости", callback_data="compatibility_menu")],
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
                await self._auto_save_analysis(user_id, analysis, "compatibility_analysis", f"{state['first_object']}↔️{state['second_object']}")
                
            else:
                await update.message.reply_text(
                    "❌ Не удалось сгенерировать анализ совместимости.\n"
                    "Попробуйте еще раз.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"compatibility_{state['analysis_type']}")
                    ]])
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка анализа совместимости: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при анализе совместимости.\n"
                "Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 К совместимости", callback_data="compatibility_menu")
                ]])
            )
    
    def _get_instructions_for_type(self, analysis_type: str) -> dict:
        """Получить инструкции для типа анализа"""
        instructions_map = {
            'companies': {
                'title': 'Компании',
                'description': 'Анализ совместимости между двумя компаниями',
                'step1': 'Введите название первой компании',
                'step2': 'Введите название второй компании'
            },
            'partner': {
                'title': 'Партнер',
                'description': 'Анализ совместимости с деловым партнером',
                'step1': 'Введите название вашей компании',
                'step2': 'Введите название компании партнера'
            },
            'employee': {
                'title': 'Сотрудник',
                'description': 'Анализ совместимости с сотрудником',
                'step1': 'Введите название вашей компании',
                'step2': 'Введите ФИО сотрудника'
            },
            'counterparty': {
                'title': 'Контрагент',
                'description': 'Анализ совместимости с контрагентом',
                'step1': 'Введите название вашей компании',
                'step2': 'Введите название контрагента'
            }
        }
        return instructions_map.get(analysis_type, instructions_map['companies'])
    
    def get_user_state(self, user_id: int) -> dict:
        """Получить состояние пользователя"""
        return self.user_states.get(user_id, {})
    
    def clear_user_state(self, user_id: int):
        """Очистить состояние пользователя"""
        if user_id in self.user_states:
            del self.user_states[user_id]
