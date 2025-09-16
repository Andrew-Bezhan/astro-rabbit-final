#!/usr/bin/env python3
# Простой тест финального исправления
import asyncio
from bot.handlers.main_router import MainRouter
from bot.states import UserData

async def test_zodiac_fix():
    """Тест исправления UserData serialization"""
    
    # Тест 1: UserData сериализация/десериализация
    print("🧪 Тест 1: UserData serialization...")
    
    user_data = UserData()
    user_data.active_company_id = 123
    
    # Сериализуем
    data_dict = user_data.to_dict()
    print(f"📊 Сериализовано: {data_dict.get('active_company_id')}")
    
    # Десериализуем
    user_data2 = UserData()
    user_data2.from_dict(data_dict)
    print(f"📊 Десериализовано: {user_data2.active_company_id}")
    
    if user_data2.active_company_id == 123:
        print("✅ Сериализация/десериализация работает!")
        return True
    else:
        print("❌ Проблема с сериализацией")
        return False

if __name__ == "__main__":
    asyncio.run(test_zodiac_fix())