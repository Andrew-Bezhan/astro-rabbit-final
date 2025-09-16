# 📋 ПОЛНЫЙ РЕЕСТР ФАЙЛОВ ПРОЕКТА ASTROBOT

## 🗂️ Основная структура проекта

### 🔧 Конфигурация и основные файлы
- `main.py` - Главная точка входа в приложение
- `main_fixed.py` - Исправленная версия main.py
- `main_optimized.py` - Оптимизированная версия main.py
- `requirements.txt` - Зависимости проекта
- `.env` - Переменные окружения (токены, API ключи)
- `.gitignore` - Файлы исключенные из git
- `astrobot.db` - База данных SQLite

### 📖 Документация
- `README.md` - Основная документация проекта
- `README_DEPLOY.md` - Руководство по развертыванию
- `README_IMPROVED.md` - Улучшенная документация
- `OPTIMIZATION_GUIDE.md` - Руководство по оптимизации
- `ASTROBOT_OPTIMIZATION_REPORT.md` - Отчет по оптимизации
- `PROMPT_ANALYSIS_REPORT.md` - Анализ промпт-системы
- `VALIDATOR_IMPROVEMENTS_REPORT.md` - Отчет по улучшениям валидации

## 🤖 Модуль AI-астролога (ai_astrologist/)

### 🧠 Основные компоненты
- `ai_astrologist/__init__.py` - Инициализация модуля
- `ai_astrologist/astro_agent.py` - **ОСНОВНОЙ AI-АГЕНТ ASTRORABBIT** 
- `ai_astrologist/openai_client.py` - Клиент OpenAI API
- `ai_astrologist/numerology.py` - Нумерологические расчеты
- `ai_astrologist/known_companies.json` - База известных компаний

### 🎯 Система промптов (ai_astrologist/prompts/)
- `ai_astrologist/prompts/__init__.py` - Инициализация промптов
- `ai_astrologist/prompts/system.py` - **СИСТЕМНЫЙ ПРОМПТ ASTRORABBIT**
- `ai_astrologist/prompts/companies.py` - **ПРОМПТЫ ДЛЯ КОМПАНИЙ (детальный алгоритм)**
- `ai_astrologist/prompts/business_forecast.py` - **БИЗНЕС-ПРОГНОЗЫ**
- `ai_astrologist/prompts/zodiac_info.py` - Информация о знаках зодиака
- `ai_astrologist/prompts/compatibility.py` - Анализ совместимости
- `ai_astrologist/prompts/daily_forecast.py` - Ежедневные прогнозы
- `ai_astrologist/prompts/financial_forecast.py` - Финансовые прогнозы
- `ai_astrologist/prompts/partnership_forecast.py` - Партнерские прогнозы
- `ai_astrologist/prompts/risk_forecast.py` - Анализ рисков
- `ai_astrologist/prompts/quick_forecast.py` - Быстрые прогнозы
- `ai_astrologist/prompts/critic_prompt.py` - **КРИТИК-ПРОМПТ ДЛЯ ОЦЕНКИ КАЧЕСТВА**

## 🤖 Модуль Telegram бота (bot/)

### 🎮 Основные компоненты
- `bot/__init__.py` - Инициализация бота
- `bot/telegram_bot.py` - **ОСНОВНОЙ TELEGRAM БОТ**
- `bot/telegram_bot_fixed.py` - Исправленная версия бота
- `bot/simple_bot.py` - Упрощенная версия бота
- `bot/keyboards.py` - Клавиатуры интерфейса
- `bot/states.py` - Состояния диалога
- `bot/custom_job_queue.py` - Кастомная очередь задач
- `bot/scheduler_config.py` - Конфигурация планировщика
- `bot/services_manager.py` - Менеджер сервисов

### 🎛️ Обработчики (bot/handlers/)
- `bot/handlers/__init__.py` - Инициализация обработчиков
- `bot/handlers/main_router.py` - **ГЛАВНЫЙ РОУТЕР**
- `bot/handlers/base_handler.py` - **БАЗОВЫЙ ОБРАБОТЧИК**
- `bot/handlers/company_handler.py` - **ОБРАБОТЧИК КОМПАНИЙ**
- `bot/handlers/zodiac_handler.py` - Обработчик знаков зодиака
- `bot/handlers/forecast_handler.py` - Обработчик прогнозов
- `bot/handlers/compatibility_handler.py` - Обработчик совместимости
- `bot/handlers/daily_handler.py` - Обработчик ежедневных прогнозов

## 📰 Модуль парсинга новостей (news_parser/)
- `news_parser/__init__.py` - Инициализация модуля
- `news_parser/news_analyzer.py` - **АНАЛИЗАТОР НОВОСТЕЙ (проблемы с timezone)**
- `news_parser/newsdata_client.py` - Клиент NewsData.io API

## 🔮 Модуль астрологических API (astrology_api/)
- `astrology_api/__init__.py` - Инициализация модуля
- `astrology_api/astro_calculations.py` - Астрологические расчеты
- `astrology_api/gpt_astro_client.py` - GPT клиент для астрологии

## 💾 Модуль базы данных (database/)
- `database/__init__.py` - Инициализация БД
- `database/connection.py` - Подключение к БД
- `database/models.py` - Модели данных SQLAlchemy
- `database/crud.py` - CRUD операции

## 🧮 Модуль векторных эмбеддингов (embedding/)
- `embedding/__init__.py` - Инициализация
- `embedding/embedding_manager.py` - Менеджер эмбеддингов
- `embedding/qdrant_client.py` - Клиент Qdrant (векторная БД)

## 🛠️ Утилиты (utils/)
- `utils/__init__.py` - Инициализация утилит
- `utils/config.py` - Конфигурация приложения
- `utils/logger.py` - Система логирования
- `utils/helpers.py` - Вспомогательные функции
- `utils/cache.py` - **СИСТЕМА КЭШИРОВАНИЯ**
- `utils/performance.py` - **МОНИТОРИНГ ПРОИЗВОДИТЕЛЬНОСТИ**
- `utils/docx_reader.py` - Чтение DOCX документов

## 🔍 Модуль валидации (validation_agent/)
- `validation_agent/__init__.py` - Инициализация агента валидации
- `validation_agent/validator.py` - Основной валидатор
- `validation_agent/orchestrator.py` - Оркестратор валидации
- `validation_agent/scorecard.py` - Система оценок
- `validation_agent/metrics_loader.py` - Загрузчик метрик
- `validation_agent/rlhf_system.py` - RLHF система
- `validation_agent/claude_validator.py` - Claude валидатор
- `validation_agent/api_client.py` - API клиент
- `validation_agent/json_parser.py` - JSON парсер
- `validation_agent/section_parser.py` - Парсер секций
- `validation_agent/patch_applier.py` - Применение патчей

## ⚙️ Конфигурация (configs/)
- `configs/scoring.yaml` - **КОНФИГУРАЦИЯ СИСТЕМЫ ОЦЕНОК**

## 🧪 Тестирование
- `bot_tester.py` - Тестер бота
- `test_openai_key.py` - Тест OpenAI ключа
- `check_instance.py` - Проверка экземпляра

## 📊 Отчеты (Reports/)
- `Reports/API_STATUS_REPORT.md` - Статус API
- `Reports/ASTROLOGY_API_READY.md` - Готовность астрологического API
- `Reports/COMMANDS_FIXED.md` - Исправленные команды
- `Reports/DATABASE_READY.md` - Готовность БД
- `Reports/ERRORS_FIXED_FINAL.md` - Финальные исправления ошибок
- `Reports/FINAL_COMMANDS_FIXED.md` - Финальные исправления команд
- `Reports/FINAL_ERRORS_RESOLVED.md` - Разрешенные ошибки
- `Reports/FINAL_REPORT.md` - Финальный отчет
- `Reports/FINAL_SUCCESS_REPORT.md` - Отчет о успехе
- `Reports/FINAL_TEST_RESULTS.md` - Результаты тестирования
- `Reports/FORMATTING_FIXED.md` - Исправления форматирования
- `Reports/NUMEROLOGY_FIXED.md` - Исправления нумерологии
- `Reports/PROJECT_STATUS.md` - Статус проекта
- `Reports/PROKERALA_API_STATUS.md` - Статус ProKerala API
- `Reports/TERMINAL_ERRORS_FIXED.md` - Исправления терминальных ошибок
- `Reports/VALIDATOR_IMPROVEMENTS_REPORT.md` - Отчет по улучшениям валидации

## 📋 Планы и документы
- `План реализации проекта.docx` - План реализации (DOCX)
- `План реализации проекта.md` - План реализации (Markdown)
- `План_реализации_проекта_readable.md` - Читаемый план
- `Промпты для AI.docx` - Промпты для AI (DOCX)

## 🎯 КЛЮЧЕВЫЕ ФАЙЛЫ ДЛЯ ОПТИМИЗАЦИИ ПРОМПТОВ:

### 🔥 КРИТИЧЕСКИ ВАЖНЫЕ:
1. **`ai_astrologist/prompts/system.py`** - Системный промпт AstroRabbit (ОСНОВА)
2. **`ai_astrologist/astro_agent.py`** - Главный AI-агент 
3. **`ai_astrologist/prompts/companies.py`** - Детальный алгоритм работы с компаниями
4. **`ai_astrologist/prompts/business_forecast.py`** - Бизнес-прогнозы

### 🎯 ВАЖНЫЕ ДЛЯ ОПТИМИЗАЦИИ:
5. **`ai_astrologist/prompts/critic_prompt.py`** - Система оценки качества
6. **`bot/handlers/base_handler.py`** - Базовая логика обработчиков
7. **`bot/handlers/company_handler.py`** - Логика работы с компаниями
8. **`news_parser/news_analyzer.py`** - Анализ новостей (проблемы с timezone)

### 🔧 ТЕХНИЧЕСКИЕ ПРОБЛЕМЫ:
- **Timezone конфигурация** в `news_parser/news_analyzer.py`
- **Алгоритм добавления компаний** в `bot/handlers/company_handler.py`
- **Валидация имен компаний** в `bot/handlers/base_handler.py`

---
**Создан:** ${new Date().toLocaleDateString('ru-RU')}  
**Цель:** Методическая оптимизация AI промпт-системы от 7.5/10 до 8.5/10