# -*- coding: utf-8 -*-
"""
Базовый класс для всех обработчиков бота
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from ..keyboards import BotKeyboards
from ..states import StateManager
from database.connection import get_session
from database.crud import UserCRUD, CompanyCRUD
from utils.helpers import validate_date, clean_company_name, is_valid_russian_name
from utils.logger import setup_logger
from utils.cache import cache_news_data, cache_astro_data, cache_company_data
from utils.performance import monitor_performance, rate_limit

logger = setup_logger()


class BaseHandler:
    """Базовый класс для всех обработчиков бота"""
    
    def __init__(self):
        """Инициализация базового обработчика"""
        self.state_manager = StateManager()
        self.keyboards = BotKeyboards()
        
        # Получаем ссылки на сервисы из менеджера (избегаем дублирования)
        from ..services_manager import ServicesManager
        services = ServicesManager.get_instance()
        
        self.astro_agent = services.astro_agent
        self.numerology = services.numerology
        self.news_analyzer = services.news_analyzer
        self.validator = services.validator
        self.embedding_manager = services.embedding_manager
        
        logger.info("✅ BaseHandler инициализирован с общими сервисами")
    
    # Общие методы для работы с данными
    
    @monitor_performance("get_news_data", slow_threshold=2.0)
    @cache_news_data(ttl=600)  # Кэшируем на 10 минут
    async def _get_news_data(self) -> str:
        """Получение актуальных новостей"""
        try:
            if self.news_analyzer:
                news_data = await self.news_analyzer.get_latest_news()
                return news_data if news_data else "Новости временно недоступны"
            return "Сервис новостей недоступен"
        except Exception as e:
            logger.warning(f"⚠️ Ошибка получения новостей: {e}")
            return "Ошибка загрузки новостей"
    
    @monitor_performance("get_daily_astrology", slow_threshold=1.0)
    @cache_astro_data(ttl=1800)  # Кэшируем на 30 минут
    async def _get_daily_astrology(self) -> str:
        """Получение астрологических данных"""
        try:
            # Здесь можно добавить получение астрологических данных
            return "Астрологические данные загружены"
        except Exception as e:
            logger.warning(f"⚠️ Ошибка получения астрологии: {e}")
            return "Астрологические данные недоступны"
    
    async def _get_company_data(self, user_id: int, company_id: str) -> Optional[Dict[str, Any]]:
        """Получение данных компании из базы"""
        try:
            user_data = self.state_manager.get_user_data(user_id)
            companies = user_data.get('companies', [])
            
            for company in companies:
                if str(company.get('id')) == str(company_id):
                    return company
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения данных компании: {e}")
            return None
    
    def _clean_html_tags(self, text: str) -> str:
        """Очистка HTML тегов из текста"""
        if not text:
            return ""
        
        # Удаляем HTML теги
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # Заменяем HTML сущности
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        clean_text = clean_text.replace('&quot;', '"')
        clean_text = clean_text.replace('&#39;', "'")
        
        return clean_text.strip()
    
    def _split_long_text(self, text: str, max_length: int = 4000) -> list:
        """Разбивка длинного текста на части"""
        if not text or len(text) <= max_length:
            return [text]
        
        parts = []
        current_part = ""
        
        # Разбиваем по абзацам
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            # Если параграф сам по себе длинный, разбиваем его
            if len(paragraph) > max_length:
                if current_part:
                    parts.append(current_part.strip())
                    current_part = ""
                
                # Разбиваем длинный параграф по предложениям
                sentences = paragraph.split('. ')
                temp_part = ""
                
                for sentence in sentences:
                    if len(temp_part + sentence) > max_length:
                        if temp_part:
                            parts.append(temp_part.strip())
                        temp_part = sentence
                    else:
                        temp_part += ". " + sentence if temp_part else sentence
                
                if temp_part:
                    current_part = temp_part
            else:
                # Если текущая часть + параграф не превышают лимит
                if len(current_part + paragraph) <= max_length:
                    current_part += "\n\n" + paragraph if current_part else paragraph
                else:
                    # Сохраняем текущую часть и начинаем новую
                    if current_part:
                        parts.append(current_part.strip())
                    current_part = paragraph
        
        # Добавляем последнюю часть
        if current_part:
            parts.append(current_part.strip())
        
        return parts if parts else [text]
    
    async def _send_long_message(self, update: Update, text: str, reply_markup=None):
        """Отправка длинного сообщения с разбивкой на части"""
        text_parts = self._split_long_text(text)
        
        if len(text_parts) == 1:
            # Короткий текст - отправляем как есть
            if update.callback_query:
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
            else:
                await update.message.reply_text(text, reply_markup=reply_markup)
        else:
            # Длинный текст - разбиваем на части
            if update.callback_query:
                # Редактируем существующее сообщение первой частью
                await update.callback_query.edit_message_text(
                    f"{text_parts[0]}\n\n📄 Часть 1 из {len(text_parts)}",
                    reply_markup=reply_markup
                )
                
                # Отправляем остальные части как новые сообщения
                for i, part in enumerate(text_parts[1:], 2):
                    await update.callback_query.message.reply_text(
                        f"{part}\n\n📄 Часть {i} из {len(text_parts)}"
                    )
            else:
                # Отправляем все части как новые сообщения
                for i, part in enumerate(text_parts, 1):
                    await update.message.reply_text(
                        f"{part}\n\n📄 Часть {i} из {len(text_parts)}",
                        reply_markup=reply_markup if i == len(text_parts) else None
                    )
    
    async def _auto_save_analysis(self, user_id: int, company_data: dict, analysis_type: str, analysis_result: str):
        """Автоматическое сохранение результата анализа"""
        try:
            user_data = self.state_manager.get_user_data(user_id)
            
            if 'saved_analyses' not in user_data:
                user_data['saved_analyses'] = []
            
            # Создаем запись анализа
            analysis_record = {
                'id': len(user_data['saved_analyses']) + 1,
                'company_name': company_data.get('name', 'Неизвестно'),
                'company_id': company_data.get('id'),
                'analysis_type': analysis_type,
                'result': analysis_result,
                'timestamp': datetime.now().isoformat(),
                'auto_saved': True
            }
            
            user_data['saved_analyses'].append(analysis_record)
            self.state_manager.save_user_data(user_id, user_data)
            
            logger.info(f"✅ Анализ {analysis_type} для компании {company_data.get('name')} автоматически сохранен")
            
        except Exception as e:
            logger.error(f"❌ Ошибка автоматического сохранения анализа: {e}")
    
    # Вспомогательные методы валидации
    
    def _validate_company_name(self, name: str) -> tuple[bool, str]:
        """Валидация названия компании согласно спецификации companies.py"""
        if not name or len(name.strip()) < 2:
            return False, "Название компании должно содержать минимум 2 символа"
        
        if len(name) > 20:
            return False, "Название компании слишком длинное (максимум 20 символов)"
        
        # Проверяем на недопустимые символы
        if not re.match(r'^[а-яА-ЯёЁa-zA-Z0-9\s\-\.\,\"\']+$', name):
            return False, "Название содержит недопустимые символы"
        
        return True, ""
    
    def _validate_registration_date(self, date_str: str) -> tuple[bool, str]:
        """Валидация даты регистрации"""
        if not date_str:
            return False, "Дата регистрации не может быть пустой"
        
        try:
            # Проверяем формат YYYY-MM-DD
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                return False, "Неверный формат даты. Используйте YYYY-MM-DD"
            
            # Проверяем, что дата не в будущем
            from datetime import datetime
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            if date_obj.date() > datetime.now().date():
                return False, "Дата регистрации не может быть в будущем"
            
            return True, ""
        except ValueError:
            return False, "Неверный формат даты"
    
    def _validate_registration_place(self, place: str) -> tuple[bool, str]:
        """Валидация места регистрации"""
        if not place or len(place.strip()) < 2:
            return False, "Место регистрации должно содержать минимум 2 символа"
        
        if len(place) > 100:
            return False, "Место регистрации слишком длинное (максимум 100 символов)"
        
        # Проверяем на недопустимые символы
        if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s\-\.]+$', place):
            return False, "Место регистрации содержит недопустимые символы"
        
        return True, ""
    
    def _validate_person_name(self, name: str) -> tuple[bool, str]:
        """Валидация имени человека"""
        if not name or len(name.strip()) < 2:
            return False, "ФИО должно содержать минимум 2 символа"
        
        if len(name) > 100:
            return False, "ФИО слишком длинное (максимум 100 символов)"
        
        # Проверяем, что имя содержит только буквы, пробелы и дефисы
        if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s\-\.]+$', name):
            return False, "ФИО содержит недопустимые символы"
        
        return True, ""
    
    def _validate_birth_date(self, date_str: str) -> tuple[bool, str]:
        """Валидация даты рождения"""
        if not date_str:
            return False, "Дата рождения не может быть пустой"
        
        try:
            # Проверяем формат YYYY-MM-DD
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                return False, "Неверный формат даты. Используйте YYYY-MM-DD"
            
            # Проверяем, что дата валидная
            from datetime import datetime
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Проверяем, что дата не в будущем
            if date_obj.date() > datetime.now().date():
                return False, "Дата рождения не может быть в будущем"
            
            # Проверяем разумный возрастной диапазон (от 18 до 100 лет)
            age = (datetime.now().date() - date_obj.date()).days / 365.25
            if age < 18:
                return False, "Возраст должен быть не менее 18 лет"
            if age > 100:
                return False, "Возраст не может превышать 100 лет"
            
            return True, ""
        except ValueError:
            return False, "Неверный формат даты"
    
    # Методы для работы с базой данных
    
    def _get_or_create_user(self, telegram_id: int, username: str = None, 
                           first_name: str = None, last_name: str = None):
        """Получение или создание пользователя в базе данных"""
        with get_session() as session:
            try:
                user = UserCRUD.get_or_create_user(
                    session, telegram_id, username, first_name, last_name
                )
                session.commit()
                # Возвращаем только ID, чтобы избежать проблем с сессией
                return user.id
            except Exception as e:
                logger.error(f"❌ Ошибка получения/создания пользователя: {e}")
                session.rollback()
                return None
    
    def _get_user_companies(self, user_id: int):
        """Получение компаний пользователя из базы данных"""
        logger.info(f"🔍 _get_user_companies вызван с user_id: {user_id} (тип: {type(user_id)})")
        
        with get_session() as session:
            try:
                # Получаем сырые данные из базы, чтобы избежать проблем с парсингом дат
                logger.info(f"🔍 Выполняем SQL запрос с параметром: {user_id}")
                
                # Используем text() для правильной обработки параметров
                from sqlalchemy import text
                result = session.execute(
                    text("SELECT id, name, registration_date, registration_place, industry, owner_name, owner_birth_date, director_name, director_birth_date, is_active "
                         "FROM companies WHERE owner_id = :user_id AND is_active = 1 ORDER BY created_at DESC"),
                    {"user_id": user_id}
                )
                
                logger.info(f"🔍 SQL запрос выполнен успешно")
                
                companies = []
                for row in result:
                    companies.append({
                        'id': row[0],
                        'name': row[1],
                        'registration_date': row[2],  # Оставляем как строку
                        'registration_place': row[3],
                        'industry': row[4],
                        'owner_name': row[5] if row[5] else None,
                        'owner_birth_date': row[6] if row[6] else None,
                        'director_name': row[7] if row[7] else None,
                        'director_birth_date': row[8] if row[8] else None,
                        'is_active': bool(row[9])
                    })
                
                logger.info(f"🔍 Получено компаний: {len(companies)}")
                
                return companies
            except Exception as e:
                logger.error(f"❌ Ошибка получения компаний пользователя: {e}")
                return []
    
    def _create_company(self, user_id: int, name: str, registration_date: datetime,
                       registration_place: str, industry: str = None, **kwargs):
        """Создание компании в базе данных"""
        with get_session() as session:
            try:
                # Сохраняем дату как строку в формате YYYY-MM-DD
                date_str = registration_date.strftime('%Y-%m-%d')
                
                # Используем сырой SQL для создания компании
                from sqlalchemy import text
                result = session.execute(
                    text("INSERT INTO companies (owner_id, name, registration_date, registration_place, industry, is_active, created_at, updated_at) "
                         "VALUES (:user_id, :name, :date_str, :registration_place, :industry, 1, datetime('now'), datetime('now'))"),
                    {
                        "user_id": user_id,
                        "name": name,
                        "date_str": date_str,
                        "registration_place": registration_place,
                        "industry": industry
                    }
                )
                session.commit()
                
                # Возвращаем данные созданной компании
                company_id = result.lastrowid
                company_data = {
                    'id': company_id,
                    'name': name,
                    'registration_date': date_str,
                    'registration_place': registration_place,
                    'industry': industry,
                    'is_active': True
                }
                
                logger.info(f"🏢 Создана компания: {name} (ID: {company_id})")
                return company_data
            except Exception as e:
                logger.error(f"❌ Ошибка создания компании: {e}")
                session.rollback()
                return None
    
    def _create_company_full(self, user_id: int, name: str, registration_date: datetime,
                            registration_place: str, industry: str = None, 
                            owner_name: str = None, owner_birth_date: datetime = None,
                            director_name: str = None, director_birth_date: datetime = None, **kwargs):
        """Создание компании в базе данных со всеми данными"""
        with get_session() as session:
            try:
                # Сохраняем даты как строки в формате YYYY-MM-DD
                reg_date_str = registration_date.strftime('%Y-%m-%d')
                owner_birth_str = owner_birth_date.strftime('%Y-%m-%d') if owner_birth_date else None
                director_birth_str = director_birth_date.strftime('%Y-%m-%d') if director_birth_date else None
                
                # Используем сырой SQL для создания компании
                from sqlalchemy import text
                result = session.execute(
                    text("INSERT INTO companies (owner_id, name, registration_date, registration_place, industry, "
                         "owner_name, owner_birth_date, director_name, director_birth_date, "
                         "is_active, created_at, updated_at) "
                         "VALUES (:user_id, :name, :reg_date_str, :registration_place, :industry, "
                         ":owner_name, :owner_birth_str, :director_name, :director_birth_str, "
                         "1, datetime('now'), datetime('now'))"),
                    {
                        "user_id": user_id,
                        "name": name,
                        "reg_date_str": reg_date_str,
                        "registration_place": registration_place,
                        "industry": industry,
                        "owner_name": owner_name,
                        "owner_birth_str": owner_birth_str,
                        "director_name": director_name,
                        "director_birth_str": director_birth_str
                    }
                )
                session.commit()
                
                # Возвращаем данные созданной компании
                company_id = result.lastrowid
                company_data = {
                    'id': company_id,
                    'name': name,
                    'registration_date': reg_date_str,
                    'registration_place': registration_place,
                    'industry': industry,
                    'owner_name': owner_name,
                    'owner_birth_date': owner_birth_str,
                    'director_name': director_name,
                    'director_birth_date': director_birth_str,
                    'is_active': True
                }
                
                logger.info(f"🏢 Создана полная компания: {name} (ID: {company_id})")
                return company_data
            except Exception as e:
                logger.error(f"❌ Ошибка создания полной компании: {e}")
                session.rollback()
                return None
    
    def _delete_company(self, company_id: int, user_id: int):
        """Удаление компании из базы данных"""
        with get_session() as session:
            try:
                # Используем сырой SQL для удаления компании
                from sqlalchemy import text
                result = session.execute(
                    text("UPDATE companies SET is_active = 0, updated_at = datetime('now') WHERE id = :company_id AND owner_id = :user_id"),
                    {"company_id": company_id, "user_id": user_id}
                )
                session.commit()
                
                success = result.rowcount > 0
                if success:
                    logger.info(f"🗑️ Компания удалена: ID {company_id}")
                else:
                    logger.warning(f"⚠️ Компания не найдена для удаления: ID {company_id}")
                
                return success
            except Exception as e:
                logger.error(f"❌ Ошибка удаления компании: {e}")
                session.rollback()
                return False
