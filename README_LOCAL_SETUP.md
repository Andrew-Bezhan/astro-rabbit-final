# 🚀 Локальная установка и запуск Astro Rabbit Bot

## 📋 Предварительные требования

### Системные требования:
- Python 3.11+
- PostgreSQL 12+
- Git

### API ключи (обязательные):
- Telegram Bot Token (от @BotFather)
- OpenAI API Key

## 🛠️ Установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/Andrew-Bezhan/astro-rabbit-final.git
cd astro-rabbit-final
```

### 2. Создание виртуального окружения
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения
```bash
# Скопируйте пример файла
cp .env.example .env

# Отредактируйте .env файл и заполните свои API ключи
nano .env
```

### 5. Настройка базы данных PostgreSQL

#### Создание базы данных:
```sql
-- Подключитесь к PostgreSQL и создайте базу
CREATE DATABASE astro_bot_db;
CREATE USER astro_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE astro_bot_db TO astro_user;
```

#### Обновите DATABASE_URL в .env:
```
DATABASE_URL=postgresql://astro_user:your_password@localhost:5432/astro_bot_db
```

## 🚀 Запуск бота

### Стандартный запуск:
```bash
python main.py
```

### Запуск с отладкой:
```bash
python main.py --debug
```

## 🔧 Конфигурация

### Обязательные переменные в .env:
- `TELEGRAM_BOT_TOKEN` - токен Telegram бота
- `OPENAI_API_KEY` - ключ OpenAI API
- `DATABASE_URL` - строка подключения к PostgreSQL

### Опциональные переменные:
- `NEWSDATA_API_KEY` - для анализа новостей
- `QDRANT_URL` + `QDRANT_API_KEY` - для векторного поиска
- `ANTHROPIC_API_KEY` - для валидации Claude

## 📊 Проверка статуса

### Проверка подключения к базе данных:
```bash
python -c "from database.connection import health_check; health_check()"
```

### Проверка API ключей:
```bash
python test_openai_key.py
```

## 🐛 Решение проблем

### Ошибка подключения к базе данных:
1. Убедитесь, что PostgreSQL запущен
2. Проверьте правильность DATABASE_URL
3. Проверьте права доступа пользователя

### Ошибка Telegram API:
1. Проверьте правильность токена бота
2. Убедитесь, что бот не запущен в другом месте
3. Проверьте интернет-соединение

### Ошибка OpenAI API:
1. Проверьте правильность API ключа
2. Убедитесь, что на счету достаточно средств
3. Проверьте лимиты запросов

## 📁 Структура проекта

```
astro-rabbit-final/
├── ai_astrologist/         # AI астрологический модуль
├── bot/                    # Telegram bot логика
├── database/              # Модели и подключение к БД
├── astrology_api/         # API астрологических расчетов
├── validation_agent/      # Система валидации ответов
├── news_parser/           # Парсер новостей
├── embedding/             # Векторный поиск
├── utils/                 # Утилиты и конфигурация
├── main.py               # Точка входа
├── requirements.txt      # Python зависимости
└── .env.example         # Пример переменных окружения
```

## 🎯 Тестирование

После запуска найдите своего бота в Telegram и отправьте `/start` для начала тестирования всех функций.