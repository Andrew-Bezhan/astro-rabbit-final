#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔬 Продвинутый тестер для глубокого анализа провалившихся функций бота
"""

import asyncio
import traceback
from datetime import datetime
from typing import Dict, Any

from bot.handlers.main_router import MainRouter
from bot.handlers.company_handler import CompanyHandler
from bot.states import BotState
from database.connection import get_session
from database.models import User, Company
from utils.logger import setup_logger

logger = setup_logger()

class DetailedMockUpdate:
    """Улучшенный мок Update для детального тестирования"""
    
    def __init__(self, user_id: int = 12345, message_text: str = "", callback_data: str = ""):
        self.effective_user = DetailedMockUser(user_id)
        self.message = DetailedMockMessage(message_text) if message_text else None
        self.callback_query = DetailedMockCallbackQuery(callback_data) if callback_data else None

class DetailedMockUser:
    """Полный мок User с всеми полями"""
    
    def __init__(self, user_id: int):
        self.id = user_id
        self.first_name = "TestUser"
        self.last_name = "TestLastName"
        self.username = "test_user"

class DetailedMockMessage:
    """Расширенный мок Message"""
    
    def __init__(self, text: str):
        self.text = text
        self.replies = []
        self.chat = DetailedMockChat()
        
    async def reply_text(self, text: str, **kwargs):
        reply = {
            'text': text,
            'kwargs': kwargs,
            'timestamp': datetime.now()
        }
        self.replies.append(reply)
        logger.info(f"📱 BOT REPLY: {text[:150]}...")
        return reply

class DetailedMockCallbackQuery:
    """Расширенный мок CallbackQuery"""
    
    def __init__(self, data: str):
        self.data = data
        self.message = DetailedMockMessage("")
        self.replies = []
    
    async def edit_message_text(self, text: str, **kwargs):
        reply = {
            'text': text,
            'kwargs': kwargs,
            'timestamp': datetime.now()
        }
        self.replies.append(reply)
        logger.info(f"✏️ BOT EDIT: {text[:150]}...")
        return reply
        
    async def answer(self, text: str = "", show_alert: bool = False):
        logger.info(f"🔔 BOT CALLBACK ANSWER: {text}")

class DetailedMockChat:
    """Мок Chat для полноты"""
    def __init__(self):
        self.id = 12345

class DetailedMockContext:
    """Расширенный мок Context"""
    
    def __init__(self):
        self.user_data = {}

class AdvancedBotTester:
    """Продвинутый тестер для детального анализа"""
    
    def __init__(self):
        self.router = MainRouter()
        self.company_handler = CompanyHandler()
        self.test_user_id = 888888  # Другой ID чтобы не конфликтовать
        logger.info("🔬 AdvancedBotTester инициализирован")
    
    async def test_companies_flow_detailed(self):
        """Детальное тестирование управления компаниями"""
        logger.info("🔬 Начинаем детальный тест companies_flow...")
        
        try:
            # 1. Показ меню компаний
            logger.info("📋 Тест 1: Показ меню компаний")
            update = DetailedMockUpdate(self.test_user_id, callback_data="companies")
            context = DetailedMockContext()
            
            await self.router.callback_handler(update, context)
            
            if update.callback_query.replies:
                logger.info("✅ Меню компаний показано успешно")
            else:
                logger.error("❌ Меню компаний не показано")
                return False
            
            # 2. Добавление новой компании
            logger.info("📋 Тест 2: Добавление новой компании")
            update2 = DetailedMockUpdate(self.test_user_id, callback_data="add_company")
            context2 = DetailedMockContext()
            
            await self.router.callback_handler(update2, context2)
            
            # 3. Ввод имени компании (симуляция)
            logger.info("📋 Тест 3: Ввод имени компании")
            update3 = DetailedMockUpdate(self.test_user_id, message_text="Тестовая IT Компания")
            
            # Устанавливаем состояние пользователя
            self.router.state_manager.set_user_state(self.test_user_id, BotState.COMPANY_NAME_INPUT)
            
            await self.router.message_handler(update3, context2)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Детальный тест companies_flow провален: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def test_zodiac_analysis_detailed(self):
        """Детальное тестирование анализа знаков зодиака"""
        logger.info("🔬 Начинаем детальный тест zodiac_analysis...")
        
        try:
            # Создаем активную компанию для пользователя
            await self.setup_test_company()
            
            # Тестируем анализ зодиака
            update = DetailedMockUpdate(self.test_user_id, callback_data="zodiac")
            context = DetailedMockContext()
            
            await self.router.callback_handler(update, context)
            
            if update.callback_query.replies:
                reply_text = update.callback_query.replies[0]['text']
                if "НЕТ АКТИВНОЙ КОМПАНИИ" in reply_text:
                    logger.error("❌ Активная компания не найдена")
                    return False
                else:
                    logger.info("✅ Анализ зодиака запущен успешно")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Детальный тест zodiac_analysis провален: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def test_compatibility_detailed(self):
        """Детальное тестирование совместимости"""
        logger.info("🔬 Начинаем детальный тест compatibility...")
        
        try:
            update = DetailedMockUpdate(self.test_user_id, callback_data="compatibility")
            context = DetailedMockContext()
            
            await self.router.callback_handler(update, context)
            
            if update.callback_query.replies:
                logger.info("✅ Меню совместимости показано")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Детальный тест compatibility провален: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def test_daily_forecast_detailed(self):
        """Детальное тестирование ежедневных прогнозов"""
        logger.info("🔬 Начинаем детальный тест daily_forecast...")
        
        try:
            update = DetailedMockUpdate(self.test_user_id, callback_data="daily")
            context = DetailedMockContext()
            
            await self.router.callback_handler(update, context)
            
            if update.callback_query.replies:
                logger.info("✅ Меню ежедневных прогнозов показано")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Детальный тест daily_forecast провален: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def test_settings_detailed(self):
        """Детальное тестирование настроек"""
        logger.info("🔬 Начинаем детальный тест settings...")
        
        try:
            update = DetailedMockUpdate(self.test_user_id, callback_data="settings")
            context = DetailedMockContext()
            
            await self.router.callback_handler(update, context)
            
            if update.callback_query.replies:
                reply_text = update.callback_query.replies[0]['text']
                if "скоро будет доступно" in reply_text.lower():
                    logger.info("✅ Настройки показывают 'скоро будет доступно'")
                    return True
                else:
                    logger.info("✅ Настройки показаны")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Детальный тест settings провален: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def setup_test_company(self):
        """Создает тестовую компанию и делает ее активной"""
        try:
            with get_session() as session:
                # Создаем пользователя если не существует
                user = session.query(User).filter_by(telegram_id=self.test_user_id).first()
                if not user:
                    user = User(
                        telegram_id=self.test_user_id,
                        username="advanced_test_user",
                        first_name="AdvancedTest"
                    )
                    session.add(user)
                    session.commit()
                
                # Создаем компанию
                test_company = Company(
                    owner_id=user.id,
                    name="Тестовая Компания Продвинутый",
                    registration_date=datetime(2020, 6, 15),  # Близнецы
                    registration_place="Санкт-Петербург",
                    industry="Технологии"
                )
                session.add(test_company)
                session.commit()
                
                # Устанавливаем как активную компанию
                user_data = self.router.state_manager.get_user_data(self.test_user_id)
                user_data['active_company_id'] = test_company.id
                self.router.state_manager.set_user_data(self.test_user_id, user_data)
                
                logger.info(f"✅ Создана тестовая компания ID: {test_company.id} для пользователя {self.test_user_id}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания тестовой компании: {e}")
    
    async def run_detailed_tests(self):
        """Запуск всех детальных тестов"""
        logger.info("🚀 Запускаем продвинутые тесты...")
        
        tests = [
            ("Companies Flow", self.test_companies_flow_detailed),
            ("Zodiac Analysis", self.test_zodiac_analysis_detailed),
            ("Compatibility", self.test_compatibility_detailed),
            ("Daily Forecast", self.test_daily_forecast_detailed),
            ("Settings", self.test_settings_detailed)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            logger.info(f"🧪 Выполняем тест: {test_name}")
            try:
                result = await test_func()
                results.append((test_name, result))
                
                if result:
                    logger.info(f"✅ {test_name} - ПРОШЕЛ")
                else:
                    logger.error(f"❌ {test_name} - ПРОВАЛЕН")
                    
            except Exception as e:
                logger.error(f"💥 {test_name} - КРИТИЧЕСКАЯ ОШИБКА: {e}")
                results.append((test_name, False))
        
        # Итоговый отчет
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        logger.info(f"""
🔬 ДЕТАЛЬНЫЙ ОТЧЕТ ПРОДВИНУТОГО ТЕСТИРОВАНИЯ
{'='*60}
📊 Всего тестов: {total}
✅ Прошло: {passed}
❌ Провалено: {total - passed}
📈 Процент успеха: {(passed/total)*100:.1f}%

📝 РЕЗУЛЬТАТЫ:
{chr(10).join([f"{'✅' if result else '❌'} {name}" for name, result in results])}
        """)
        
        return results

async def main():
    """Запуск продвинутого тестирования"""
    try:
        logger.info("🔬 Запуск продвинутого тестера...")
        
        tester = AdvancedBotTester()
        await tester.run_detailed_tests()
        
        logger.info("✅ Продвинутое тестирование завершено!")
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка продвинутого тестирования: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())