#!/usr/bin/env python3
# Финальный быстрый тест для проверки исправления
import asyncio
from advanced_bot_tester import AdvancedBotTester

async def main():
    tester = AdvancedBotTester()
    result = await tester.test_zodiac_analysis_detailed()
    if result:
        print("🎉 ZODIAC ANALYSIS FIXED!")
    else:
        print("❌ Still failing")

if __name__ == "__main__":
    asyncio.run(main())