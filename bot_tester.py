#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Интерактивный тестер всех функций бота в терминале
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.handlers.company_handler import CompanyHandler
from bot.handlers.zodiac_handler import ZodiacHandler
from bot.handlers.compatibility_handler import CompatibilityHandler
from bot.handlers.daily_handler import DailyHandler
from bot.handlers.forecast_handler import ForecastHandler
from bot.states import BotState
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger()

class MockUpdate:
    """Мок объект для Update"""
    def __init__(self, user_id=808868292, text="", callback_data="", username="andrew_bezhan"):
        self.effective_user = MockUser(user_id, username)
        self.message = MockMessage(text) if text else None
        self.callback_query = MockCallbackQuery(callback_data) if callback_data else None

class MockUser:
    """Мок объект для User"""
    def __init__(self, user_id, username="andrew_bezhan"):
        self.id = user_id
        self.username = username
        self.first_name = "Andrew"
        self.last_name = "Bezhan"

class MockMessage:
    """Мок объект для Message"""
    def __init__(self, text):
        self.text = text
    
    async def reply_text(self, text, **kwargs):
        print(f"\n📱 БОТ ОТВЕЧАЕТ:")
        print(f"   {text}")
        if kwargs.get('reply_markup'):
            print(f"   🔘 Кнопки: {kwargs['reply_markup']}")

class MockCallbackQuery:
    """Мок объект для CallbackQuery"""
    def __init__(self, data):
        self.data = data
        self.from_user = MockUser(808868292)
    
    async def edit_message_text(self, text, **kwargs):
        print(f"\n📱 БОТ ОБНОВЛЯЕТ СООБЩЕНИЕ:")
        print(f"   {text}")
        if kwargs.get('reply_markup'):
            print(f"   🔘 Кнопки: {kwargs['reply_markup']}")

class MockContext:
    """Мок объект для Context"""
    def __init__(self):
        self.user_data = {}

class BotTester:
    """Интерактивный тестер функций бота"""
    
    def __init__(self):
        self.company_handler = CompanyHandler()
        self.zodiac_handler = ZodiacHandler()
        self.compatibility_handler = CompatibilityHandler()
        self.daily_handler = DailyHandler()
        self.forecast_handler = ForecastHandler()
        self.context = MockContext()
        self.user_id = 808868292
        
    def print_menu(self):
        """Показать главное меню тестера"""
        print("\n" + "="*60)
        print("🤖 ИНТЕРАКТИВНЫЙ ТЕСТЕР АСТРО-БОТА")
        print("="*60)
        print("1️⃣  Тестировать 'Мои компании'")
        print("2️⃣  Тестировать 'Добавить компанию' (полный цикл)")
        print("3️⃣  Тестировать 'Знак зодиака'")
        print("4️⃣  Тестировать 'Совместимость'")
        print("5️⃣  Тестировать 'Ежедневный прогноз'")
        print("6️⃣  Тестировать 'Бизнес-прогноз'")
        print("7️⃣  Показать базу данных")
        print("8️⃣  Очистить базу данных")
        print("0️⃣  Выход")
        print("="*60)
    
    async def test_companies_menu(self):
        """Тестирование меню компаний"""
        print("\n🧪 ТЕСТИРУЕМ: Мои компании")
        update = MockUpdate(callback_data="companies")
        await self.company_handler.show_companies_menu(update, self.context)
    
    async def test_add_company_full_cycle(self):
        """Тестирование полного цикла добавления компании"""
        print("\n🧪 ТЕСТИРУЕМ: Полный цикл добавления компании")
        
        # Шаг 1: Начало добавления
        print("\n1️⃣ Начинаем добавление компании...")
        update = MockUpdate(callback_data="add_company")
        await self.company_handler.start_add_company(update, self.context)
        
        # Шаг 2: Ввод названия
        company_name = input("\n📝 Введите название компании: ").strip()
        if not company_name:
            company_name = "ООО Тестовая Компания"
            print(f"   Используем по умолчанию: {company_name}")
        
        update = MockUpdate(text=company_name)
        await self.company_handler.handle_company_name_input(update, self.context, company_name)
        
        # Шаг 3: Ввод даты регистрации
        reg_date = input("\n📅 Введите дату регистрации (YYYY-MM-DD): ").strip()
        if not reg_date:
            reg_date = "2020-05-15"
            print(f"   Используем по умолчанию: {reg_date}")
        
        update = MockUpdate(text=reg_date)
        await self.company_handler.handle_registration_date_input(update, self.context, reg_date)
        
        # Шаг 4: Ввод места регистрации
        reg_place = input("\n📍 Введите место регистрации: ").strip()
        if not reg_place:
            reg_place = "Москва"
            print(f"   Используем по умолчанию: {reg_place}")
        
        update = MockUpdate(text=reg_place)
        await self.company_handler.handle_registration_place_input(update, self.context, reg_place)
        
        # Шаг 5: Выбор сферы
        print("\n🏭 Выберите сферу деятельности:")
        print("1 - Строительство и промышленность")
        print("2 - Финансы и инвестиции") 
        print("3 - Торговля и сфера услуг")
        print("4 - Технологии и телекоммуникации")
        print("5 - Государственный сектор")
        print("6 - Энергетика")
        
        sphere_choice = input("Выбор (1-6): ").strip()
        sphere_map = {
            "1": "sphere_construction",
            "2": "sphere_finance", 
            "3": "sphere_trade",
            "4": "sphere_tech",
            "5": "sphere_government",
            "6": "sphere_energy"
        }
        
        sphere = sphere_map.get(sphere_choice, "sphere_tech")
        print(f"   Выбрано: {sphere}")
        
        update = MockUpdate(callback_data=sphere)
        await self.company_handler.handle_sphere_selection(update, self.context, sphere)
        
        # Шаг 6: Ввод ФИО собственника
        owner_name = input("\n👤 Введите ФИО собственника: ").strip()
        if not owner_name:
            owner_name = "Иванов Иван Иванович"
            print(f"   Используем по умолчанию: {owner_name}")
        
        update = MockUpdate(text=owner_name)
        await self.company_handler.handle_owner_name_input(update, self.context, owner_name)
        
        # Шаг 7: Ввод даты рождения собственника
        owner_birth = input("\n📅 Введите дату рождения собственника (YYYY-MM-DD): ").strip()
        if not owner_birth:
            owner_birth = "1980-05-15"
            print(f"   Используем по умолчанию: {owner_birth}")
        
        update = MockUpdate(text=owner_birth)
        await self.company_handler.handle_owner_birth_input(update, self.context, owner_birth)
        
        # Шаг 8: Ввод ФИО директора
        director_name = input("\n👔 Введите ФИО директора: ").strip()
        if not director_name:
            director_name = "Петров Петр Петрович"
            print(f"   Используем по умолчанию: {director_name}")
        
        update = MockUpdate(text=director_name)
        await self.company_handler.handle_director_name_input(update, self.context, director_name)
        
        # Шаг 9: Ввод даты рождения директора
        director_birth = input("\n📅 Введите дату рождения директора (YYYY-MM-DD): ").strip()
        if not director_birth:
            director_birth = "1975-08-20"
            print(f"   Используем по умолчанию: {director_birth}")
        
        update = MockUpdate(text=director_birth)
        await self.company_handler.handle_director_birth_input(update, self.context, director_birth)
        
        print("\n✅ ПОЛНЫЙ ЦИКЛ ДОБАВЛЕНИЯ КОМПАНИИ ЗАВЕРШЕН!")
    
    async def test_zodiac(self):
        """Тестирование функции знака зодиака"""
        print("\n🧪 ТЕСТИРУЕМ: Знак зодиака")
        update = MockUpdate(callback_data="zodiac")
        await self.zodiac_handler.show_zodiac_menu(update, self.context)
    
    async def test_compatibility(self):
        """Тестирование функции совместимости"""
        print("\n🧪 ТЕСТИРУЕМ: Совместимость")
        update = MockUpdate(callback_data="compatibility")
        await self.compatibility_handler.show_compatibility_menu(update, self.context)
    
    async def test_daily(self):
        """Тестирование ежедневного прогноза"""
        print("\n🧪 ТЕСТИРУЕМ: Ежедневный прогноз")
        update = MockUpdate(callback_data="daily")
        await self.daily_handler.show_daily_menu(update, self.context)
    
    async def test_forecast(self):
        """Тестирование бизнес-прогноза"""
        print("\n🧪 ТЕСТИРУЕМ: Бизнес-прогноз")
        update = MockUpdate(callback_data="forecast")
        await self.forecast_handler.show_forecast_menu(update, self.context)
    
    def show_database(self):
        """Показать содержимое базы данных"""
        print("\n🧪 ПОКАЗЫВАЕМ: Содержимое базы данных")
        
        from database.connection import get_session
        from sqlalchemy import text
        
        with get_session() as session:
            try:
                # Показываем пользователей
                result = session.execute(text("SELECT id, telegram_id, username, first_name, last_name FROM users"))
                users = result.fetchall()
                
                print(f"\n👥 ПОЛЬЗОВАТЕЛИ ({len(users)}):")
                for user in users:
                    print(f"   ID: {user[0]}, TG: {user[1]}, @{user[2]}, {user[3]} {user[4]}")
                
                # Показываем компании
                result = session.execute(text("SELECT id, owner_id, name, registration_date, registration_place, industry, owner_name, director_name FROM companies WHERE is_active = 1"))
                companies = result.fetchall()
                
                print(f"\n🏢 КОМПАНИИ ({len(companies)}):")
                for company in companies:
                    print(f"   ID: {company[0]}, Owner: {company[1]}")
                    print(f"      Название: {company[2]}")
                    print(f"      Дата: {company[3]}, Место: {company[4]}")
                    print(f"      Отрасль: {company[5]}")
                    print(f"      Собственник: {company[6]}")
                    print(f"      Директор: {company[7]}")
                    print()
                    
            except Exception as e:
                print(f"❌ Ошибка: {e}")
    
    def clear_database(self):
        """Очистить базу данных"""
        confirm = input("\n⚠️  ВНИМАНИЕ! Очистить ВСЮ базу данных? (да/нет): ").strip().lower()
        
        if confirm in ['да', 'yes', 'y']:
            from database.connection import get_session
            from sqlalchemy import text
            
            with get_session() as session:
                try:
                    # Очищаем компании
                    result = session.execute(text("DELETE FROM companies"))
                    companies_deleted = result.rowcount
                    
                    # Очищаем пользователей
                    result = session.execute(text("DELETE FROM users"))
                    users_deleted = result.rowcount
                    
                    session.commit()
                    
                    print(f"✅ Удалено:")
                    print(f"   🏢 Компаний: {companies_deleted}")
                    print(f"   👥 Пользователей: {users_deleted}")
                    
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
                    session.rollback()
        else:
            print("❌ Очистка отменена")
    
    async def run(self):
        """Запуск интерактивного тестера"""
        print("\n🚀 ЗАПУСК ИНТЕРАКТИВНОГО ТЕСТЕРА АСТРО-БОТА")
        
        while True:
            self.print_menu()
            choice = input("\nВыберите функцию для тестирования: ").strip()
            
            try:
                if choice == "1":
                    await self.test_companies_menu()
                elif choice == "2":
                    await self.test_add_company_full_cycle()
                elif choice == "3":
                    await self.test_zodiac()
                elif choice == "4":
                    await self.test_compatibility()
                elif choice == "5":
                    await self.test_daily()
                elif choice == "6":
                    await self.test_forecast()
                elif choice == "7":
                    self.show_database()
                elif choice == "8":
                    self.clear_database()
                elif choice == "0":
                    print("\n👋 Выход из тестера")
                    break
                else:
                    print("❌ Неверный выбор. Попробуйте еще раз.")
                    
            except Exception as e:
                print(f"\n❌ ОШИБКА ПРИ ТЕСТИРОВАНИИ: {e}")
                import traceback
                traceback.print_exc()
            
            input("\n⏸️  Нажмите Enter для продолжения...")

async def main():
    """Главная функция"""
    tester = BotTester()
    await tester.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

