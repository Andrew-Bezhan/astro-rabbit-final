#!/usr/bin/env python3
"""
Тест загрузки OpenAI API ключа из .env файла
"""

import os
from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()

# Проверяем переменные окружения
openai_key = os.getenv('OPENAI_API_KEY', 'НЕ НАЙДЕН')
print(f"🔑 OPENAI_API_KEY из .env: {openai_key}")
print(f"📏 Длина ключа: {len(openai_key)} символов")

# Проверяем, начинается ли с правильного префикса
if openai_key.startswith('sk-proj-'):
    print("✅ Ключ имеет правильный формат (sk-proj-)")
else:
    print("❌ Ключ НЕ имеет правильный формат OpenAI")

# Тестируем загрузку через наш config
try:
    from utils.config import load_config
    config = load_config()
    print(f"🛠️ Через load_config(): {config.openai.api_key}")
    print(f"📏 Длина через config: {len(config.openai.api_key)} символов")
    
    if config.openai.api_key == openai_key:
        print("✅ Конфигурация загружается правильно")
    else:
        print("❌ Конфигурация загружается НЕПРАВИЛЬНО")
        
except Exception as e:
    print(f"❌ Ошибка загрузки конфигурации: {e}")

# Тестируем инициализацию OpenAI клиента
try:
    import openai
    client = openai.OpenAI(api_key=openai_key)
    print("✅ OpenAI клиент создан успешно")
    
    # Простой тест API
    try:
        response = client.models.list()
        print("✅ API ключ работает - список моделей получен")
        models = [model.id for model in response.data[:3]]
        print(f"📋 Доступные модели: {models}")
    except Exception as api_error:
        print(f"❌ API ключ НЕ работает: {api_error}")
        
except Exception as e:
    print(f"❌ Ошибка создания OpenAI клиента: {e}")
