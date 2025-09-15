# -*- coding: utf-8 -*-
"""
Обработчик для управления компаниями
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from .base_handler import BaseHandler
from ..states import BotState
from ai_astrologist.prompts import COMPANY_ZODIAC_INFO_PROMPT
from database.connection import get_session
from database.crud import CompanyCRUD
from utils.helpers import validate_date, clean_company_name, is_valid_russian_name
from utils.logger import setup_logger

logger = setup_logger()


class CompanyHandler(BaseHandler):
    """Обработчик для управления компаниями"""
    
    async def show_companies_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню управления компаниями"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        query = update.callback_query
        
        try:
            # Получаем пользователя из базы данных
            user_id_db = self._get_or_create_user(
                user_id, 
                update.effective_user.username,
                update.effective_user.first_name,
                update.effective_user.last_name
            )
            
            if not user_id_db:
                await query.edit_message_text(
                    "❌ Ошибка получения данных пользователя",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main_menu")]
                    ])
                )
                return
            
            logger.info(f"🔍 Получаем компании для пользователя ID: {user_id_db}")
            
            # Получаем список компаний пользователя из базы данных
            companies = self._get_user_companies(user_id_db)
            
            if not companies:
                # Нет компаний - предлагаем добавить
                await query.edit_message_text(
                    "🏢 <b>МОИ КОМПАНИИ</b>\n\n"
                    "У вас пока нет сохраненных компаний.\n"
                    "Добавьте компанию, чтобы получать персональные прогнозы!",
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ Добавить компанию", callback_data="add_company")],
                        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main_menu")]
                    ])
                )
            else:
                # Показываем список компаний (ограничиваем количество для удобства)
                companies_text = f"🏢 <b>МОИ КОМПАНИИ</b> ({len(companies)} компаний)\n\n"
                
                # Показываем только первые 10 компаний
                display_companies = companies[:10]
                for i, company in enumerate(display_companies, 1):
                    companies_text += f"🏢 {i}. <b>{company['name']}</b>\n"
                    companies_text += f"   📅 {company['registration_date']}\n"
                    companies_text += f"   📍 {company['registration_place']}\n"
                    if company.get('industry'):
                        companies_text += f"   🏭 {company['industry']}\n"
                    if company.get('owner_name'):
                        companies_text += f"   👤 {company['owner_name']}\n"
                    if company.get('director_name'):
                        companies_text += f"   👔 {company['director_name']}\n"
                    companies_text += "\n"
                
                if len(companies) > 10:
                    companies_text += f"... и еще {len(companies) - 10} компаний\n\n"
                
                # Создаем клавиатуру с компаниями (только первые 5 для экономии места)
                keyboard = []
                for company in display_companies[:5]:
                    company_name = company['name'][:20]  # Ограничиваем длину
                    keyboard.append([
                        InlineKeyboardButton(
                            f"🏢 {company_name}",
                            callback_data=f"select_company_{company['id']}"
                        )
                    ])
                
                # Добавляем кнопки управления
                keyboard.extend([
                    [InlineKeyboardButton("➕ Добавить компанию", callback_data="add_company")],
                    [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main_menu")]
                ])
                
                await query.edit_message_text(
                    companies_text,
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка показа меню компаний: {e}")
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main_menu")]
                ])
            )
    
    async def start_add_company(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать процесс добавления новой компании"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        query = update.callback_query
        
        try:
            # Сбрасываем состояние
            self.state_manager.set_user_state(user_id, BotState.COMPANY_NAME_INPUT)
            context.user_data['adding_company'] = True
            context.user_data['new_company'] = {}
            
            await query.edit_message_text(
                "🏢 <b>ДОБАВЛЕНИЕ КОМПАНИИ</b>\n\n"
                "Введите название компании:",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data="companies_menu")]
                ])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка начала добавления компании: {e}")
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                ])
            )
    
    async def handle_company_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Обработка ввода названия компании"""
        if not update.effective_user:
            return
            
        user_id = update.effective_user.id
        
        try:
            # Валидируем название
            is_valid, error_msg = self._validate_company_name(text)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ {error_msg}\n\nПопробуйте еще раз:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("❌ Отмена", callback_data="companies_menu")]
                    ])
                )
                return
            
            # Сохраняем название
            context.user_data['new_company']['name'] = text.strip()
            
            # Переходим к вводу даты регистрации
            self.state_manager.set_user_state(user_id, BotState.COMPANY_REG_DATE_INPUT)
            
            await update.message.reply_text(
                "📅 <b>ДАТА РЕГИСТРАЦИИ</b>\n\n"
                "Введите дату регистрации компании в формате YYYY-MM-DD\n"
                "Например: 2020-05-15",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data="companies_menu")]
                ])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки названия компании: {e}")
            await update.message.reply_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                ])
            )
    
    async def handle_registration_date_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Обработка ввода даты регистрации"""
        if not update.effective_user:
            return
            
        user_id = update.effective_user.id
        
        try:
            # Валидируем дату
            is_valid, error_msg = self._validate_registration_date(text)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ {error_msg}\n\nПопробуйте еще раз:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("❌ Отмена", callback_data="companies_menu")]
                    ])
                )
                return
            
            # Сохраняем дату
            context.user_data['new_company']['reg_date'] = text.strip()
            
            # Переходим к вводу места регистрации
            self.state_manager.set_user_state(user_id, BotState.COMPANY_REG_PLACE_INPUT)
            
            await update.message.reply_text(
                "📍 <b>МЕСТО РЕГИСТРАЦИИ</b>\n\n"
                "Введите город регистрации компании:\n"
                "Например: Москва, Санкт-Петербург, Новосибирск",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data="companies_menu")]
                ])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки даты регистрации: {e}")
            await update.message.reply_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                ])
            )
    
    async def handle_registration_place_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Обработка ввода места регистрации"""
        if not update.effective_user:
            return
            
        user_id = update.effective_user.id
        
        try:
            # Валидируем место регистрации
            is_valid, error_msg = self._validate_registration_place(text)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ {error_msg}\n\nПопробуйте еще раз:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("❌ Отмена", callback_data="companies_menu")]
                    ])
                )
                return
            
            # Сохраняем место регистрации
            context.user_data['new_company']['reg_place'] = text.strip()
            
            # Переходим к выбору сферы деятельности
            self.state_manager.set_user_state(user_id, BotState.COMPANY_SPHERE_SELECTION)
            
            await update.message.reply_text(
                "🏭 <b>СФЕРА ДЕЯТЕЛЬНОСТИ</b>\n\n"
                "Выберите сферу деятельности компании:",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏗️ Строительство и промышленность", callback_data="sphere_construction")],
                    [InlineKeyboardButton("💰 Финансы и инвестиции", callback_data="sphere_finance")],
                    [InlineKeyboardButton("🛒 Торговля и сфера услуг", callback_data="sphere_trade")],
                    [InlineKeyboardButton("💻 Технологии и телекоммуникации", callback_data="sphere_tech")],
                    [InlineKeyboardButton("🏛️ Государственный сектор", callback_data="sphere_government")],
                    [InlineKeyboardButton("⚡ Энергетика", callback_data="sphere_energy")],
                    [InlineKeyboardButton("❌ Отмена", callback_data="companies_menu")]
                ])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки места регистрации: {e}")
            await update.message.reply_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                ])
            )
    
    async def handle_sphere_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Обработка выбора сферы деятельности"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        query = update.callback_query
        
        try:
            # Получаем пользователя из базы данных
            user_id_db = self._get_or_create_user(
                user_id, 
                update.effective_user.username,
                update.effective_user.first_name,
                update.effective_user.last_name
            )
            
            if not user_id_db:
                await query.edit_message_text(
                    "❌ Ошибка получения данных пользователя",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main_menu")]
                    ])
                )
                return
            
            # Сохраняем сферу деятельности
            context.user_data['new_company']['industry'] = callback_data.replace('sphere_', '').title()
            
            # Переходим к вводу данных собственника
            self.state_manager.set_user_state(user_id, BotState.COMPANY_OWNER_NAME_INPUT)
            
            await query.edit_message_text(
                "👤 <b>ДАННЫЕ СОБСТВЕННИКА</b>\n\n"
                "Введите ФИО собственника компании:\n"
                "Например: Иванов Иван Иванович",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data="companies_menu")]
                ])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки выбора сферы: {e}")
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                ])
            )
    
    async def handle_owner_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Обработка ввода ФИО собственника"""
        if not update.effective_user:
            return
            
        user_id = update.effective_user.id
        
        try:
            # Валидируем ФИО
            is_valid, error_msg = self._validate_person_name(text)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ {error_msg}\n\nПопробуйте еще раз:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("❌ Отмена", callback_data="companies_menu")]
                    ])
                )
                return
            
            # Сохраняем ФИО собственника
            context.user_data['new_company']['owner_name'] = text.strip()
            
            # Переходим к вводу даты рождения собственника
            self.state_manager.set_user_state(user_id, BotState.COMPANY_OWNER_BIRTH_INPUT)
            
            await update.message.reply_text(
                "📅 <b>ДАТА РОЖДЕНИЯ СОБСТВЕННИКА</b>\n\n"
                "Введите дату рождения собственника в формате YYYY-MM-DD\n"
                "Например: 1980-05-15",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data="companies_menu")]
                ])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки ФИО собственника: {e}")
            await update.message.reply_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                ])
            )
    
    async def handle_owner_birth_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Обработка ввода даты рождения собственника"""
        if not update.effective_user:
            return
            
        user_id = update.effective_user.id
        
        try:
            # Валидируем дату
            is_valid, error_msg = self._validate_birth_date(text)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ {error_msg}\n\nПопробуйте еще раз:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("❌ Отмена", callback_data="companies_menu")]
                    ])
                )
                return
            
            # Сохраняем дату рождения собственника
            context.user_data['new_company']['owner_birth_date'] = text.strip()
            
            # Переходим к вводу данных директора
            self.state_manager.set_user_state(user_id, BotState.COMPANY_DIRECTOR_NAME_INPUT)
            
            await update.message.reply_text(
                "👔 <b>ДАННЫЕ ДИРЕКТОРА</b>\n\n"
                "Введите ФИО директора компании:\n"
                "Например: Петров Петр Петрович\n\n"
                "💡 <i>Если собственник и директор - одно лицо, введите те же данные</i>",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data="companies_menu")]
                ])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки даты рождения собственника: {e}")
            await update.message.reply_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                ])
            )
    
    async def handle_director_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Обработка ввода ФИО директора"""
        if not update.effective_user:
            return
            
        user_id = update.effective_user.id
        
        try:
            # Валидируем ФИО
            is_valid, error_msg = self._validate_person_name(text)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ {error_msg}\n\nПопробуйте еще раз:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("❌ Отмена", callback_data="companies_menu")]
                    ])
                )
                return
            
            # Сохраняем ФИО директора
            context.user_data['new_company']['director_name'] = text.strip()
            
            # Переходим к вводу даты рождения директора
            self.state_manager.set_user_state(user_id, BotState.COMPANY_DIRECTOR_BIRTH_INPUT)
            
            await update.message.reply_text(
                "📅 <b>ДАТА РОЖДЕНИЯ ДИРЕКТОРА</b>\n\n"
                "Введите дату рождения директора в формате YYYY-MM-DD\n"
                "Например: 1975-08-20",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data="companies_menu")]
                ])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки ФИО директора: {e}")
            await update.message.reply_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                ])
            )
    
    async def handle_director_birth_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Обработка ввода даты рождения директора"""
        if not update.effective_user:
            return
            
        user_id = update.effective_user.id
        
        try:
            # Валидируем дату
            is_valid, error_msg = self._validate_birth_date(text)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ {error_msg}\n\nПопробуйте еще раз:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("❌ Отмена", callback_data="companies_menu")]
                    ])
                )
                return
            
            # Сохраняем дату рождения директора
            context.user_data['new_company']['director_birth_date'] = text.strip()
            
            # Теперь создаем компанию со всеми данными
            user_id_db = self._get_or_create_user(
                user_id, 
                update.effective_user.username,
                update.effective_user.first_name,
                update.effective_user.last_name
            )
            
            if not user_id_db:
                await update.message.reply_text(
                    "❌ Ошибка получения данных пользователя",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main_menu")]
                    ])
                )
                return
            
            # Получаем все данные новой компании
            new_company_data = context.user_data.get('new_company', {})
            
            # Создаем компанию в базе данных со всеми данными
            company = self._create_company_full(
                user_id=user_id_db,
                name=new_company_data.get('name'),
                registration_date=datetime.strptime(new_company_data.get('reg_date'), '%Y-%m-%d'),
                registration_place=new_company_data.get('reg_place'),
                industry=new_company_data.get('industry'),
                owner_name=new_company_data.get('owner_name'),
                owner_birth_date=datetime.strptime(new_company_data.get('owner_birth_date'), '%Y-%m-%d'),
                director_name=new_company_data.get('director_name'),
                director_birth_date=datetime.strptime(new_company_data.get('director_birth_date'), '%Y-%m-%d')
            )
            
            if not company:
                await update.message.reply_text(
                    "❌ Ошибка создания компании",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                    ])
                )
                return
            
            # Сбрасываем состояние
            self.state_manager.set_user_state(user_id, BotState.MAIN_MENU)
            context.user_data.pop('adding_company', None)
            context.user_data.pop('new_company', None)
            
            await update.message.reply_text(
                f"✅ <b>КОМПАНИЯ ДОБАВЛЕНА!</b>\n\n"
                f"🏢 <b>{company['name']}</b>\n"
                f"📅 Дата регистрации: {company['registration_date']}\n"
                f"📍 Место регистрации: {company['registration_place']}\n"
                f"🏭 Сфера деятельности: {company['industry']}\n"
                f"👤 Собственник: {company['owner_name']}\n"
                f"👔 Директор: {company['director_name']}\n\n"
                "Компания сохранена и готова для анализа!",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏢 Мои компании", callback_data="companies_menu")],
                    [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main_menu")]
                ])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки даты рождения директора: {e}")
            await update.message.reply_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                ])
            )
    
    async def select_company(self, update: Update, context: ContextTypes.DEFAULT_TYPE, company_id: str):
        """Выбор компании для действий"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        query = update.callback_query
        
        try:
            # Получаем данные компании
            company_data = await self._get_company_data(user_id, company_id)
            if not company_data:
                await query.edit_message_text(
                    "❌ Данные компании не найдены.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                    ])
                )
                return
            
            # Показываем меню действий с компанией
            company_name = company_data.get('name', 'Неизвестно')
            
            await query.edit_message_text(
                f"🏢 <b>{company_name}</b>\n\nВыберите действие:",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⭐ Сделать активной", callback_data=f"set_active_company_{company_id}")],
                    [InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_company_{company_id}")],
                    [InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_company_{company_id}")],
                    [InlineKeyboardButton("🔙 К списку компаний", callback_data="companies_menu")]
                ])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка выбора компании: {e}")
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                ])
            )
    
    async def set_active_company(self, update: Update, context: ContextTypes.DEFAULT_TYPE, company_id: str):
        """Установка активной компании"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        query = update.callback_query
        
        try:
            # Получаем данные пользователя
            user_data = self.state_manager.get_user_data(user_id)
            
            # Устанавливаем активную компанию
            user_data['active_company_id'] = company_id
            
            # Сохраняем данные
            self.state_manager.save_user_data(user_id, user_data)
            
            # Получаем данные компании для отображения
            company_data = await self._get_company_data(user_id, company_id)
            company_name = company_data.get('name', 'Неизвестно') if company_data else 'Неизвестно'
            
            await query.edit_message_text(
                f"✅ <b>АКТИВНАЯ КОМПАНИЯ УСТАНОВЛЕНА</b>\n\n"
                f"🏢 <b>{company_name}</b>\n\n"
                "Теперь все прогнозы будут составляться для этой компании!",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏢 Мои компании", callback_data="companies_menu")],
                    [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main_menu")]
                ])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка установки активной компании: {e}")
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                ])
            )
    
    async def delete_company(self, update: Update, context: ContextTypes.DEFAULT_TYPE, company_id: str):
        """Удаление компании"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        query = update.callback_query
        
        try:
            # Получаем пользователя из базы данных
            user_id_db = self._get_or_create_user(
                user_id, 
                update.effective_user.username,
                update.effective_user.first_name,
                update.effective_user.last_name
            )
            
            if not user_id_db:
                await query.edit_message_text(
                    "❌ Ошибка получения данных пользователя",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                    ])
                )
                return
            
            # Получаем компанию из базы данных
            with get_session() as session:
                from sqlalchemy import text
                result = session.execute(
                    text("SELECT name FROM companies WHERE id = :company_id AND owner_id = :user_id AND is_active = 1"),
                    {"company_id": int(company_id), "user_id": user_id_db}
                )
                company_row = result.fetchone()
                
                if not company_row:
                    await query.edit_message_text(
                        "❌ Компания не найдена.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                        ])
                    )
                    return
                
                company_name = company_row[0]
                
                # Удаляем компанию из базы данных
                success = self._delete_company(int(company_id), user_id_db)
                
                if not success:
                    await query.edit_message_text(
                        "❌ Ошибка удаления компании.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                        ])
                    )
                    return
            
            await query.edit_message_text(
                f"✅ <b>КОМПАНИЯ УДАЛЕНА</b>\n\n"
                f"🏢 <b>{company_name}</b>\n\n"
                "Компания успешно удалена из вашего списка.",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏢 Мои компании", callback_data="companies_menu")],
                    [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main_menu")]
                ])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка удаления компании: {e}")
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К компаниям", callback_data="companies_menu")]
                ])
            )
