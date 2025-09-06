"""
Агент-валидатор на базе Claude-3.5-Sonnet от Anthropic
"""

import os
import aiohttp
import json
import traceback
from typing import Dict, Any, List, Tuple
from utils.logger import setup_logger

logger = setup_logger()


class ClaudeValidatorAgent:
    """Продвинутый валидатор на Claude-3.5-Sonnet"""
    
    def __init__(self):
        """Инициализация Claude валидатора"""
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.model = "claude-3-5-sonnet-20241022"
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.max_tokens = 2000
        
        if self.api_key:
            logger.info("✅ Claude валидатор инициализирован")
        else:
            logger.warning("⚠️ ANTHROPIC_API_KEY не найден в .env")
    
    async def validate_and_score(self, text: str, original_prompt: str, analysis_type: str = "zodiac") -> Dict[str, Any]:
        """
        Валидация и оценка текста через Claude
        """
        if not self.api_key:
            return {
                'score': 5.0,
                'is_valid': False,
                'issues': ['API ключ не настроен'],
                'suggestions': [],
                'fixed_text': text
            }
        
        validation_prompt = f"""
Ты - строгий валидатор текстов для Telegram бота. Оцени этот астрологический анализ от 1 до 10.

КРИТЕРИИ ОЦЕНКИ:

1. ФОРМАТИРОВАНИЕ (КРИТИЧНО):
- HTML теги (<p>, <h1>, <b>, <i>) = 0 баллов
- Markdown (**, __, ##, ---) = 0 баллов  
- Правильные заголовки с эмодзи "🌟 Название" = +2 балла
- Списки с эмодзи (⭐, 🎯, 💫) вместо • или * = +2 балла

2. СТРУКТУРА (КРИТИЧНО):
Должно быть 6 блоков:
🌟 ВЛИЯНИЕ ЗНАКА ЗОДИАКА НА КОМПАНИЮ
🔮 ПЛАНЕТАРНОЕ ВЛИЯНИЕ И ГЕОГРАФИЯ
💎 СИЛЬНЫЕ СТОРОНЫ И ПОТЕНЦИАЛ
🧘 ФИЛОСОФИЯ И КОНЦЕПЦИЯ БИЗНЕСА
⚠️ РИСКИ И НОВОСТНОЙ КОНТЕКСТ
💼 РЕКОМЕНДАЦИИ И ПРИМЕРЫ КОМПАНИЙ

3. СОДЕРЖАНИЕ (КРИТИЧНО):
- Упоминание конкретных новостей = +2 балла
- Примеры известных компаний = +2 балла
- Профессиональный тон = +2 балла

ВЕРНИ ТОЛЬКО ЧИСЛО ОТ 1 ДО 10. Например: 8.5

ТЕКСТ ДЛЯ ОЦЕНКИ:
{text}
"""
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'x-api-key': self.api_key,
                    'content-type': 'application/json',
                    'anthropic-version': '2023-06-01'
                }
                
                payload = {
                    'model': self.model,
                    'max_tokens': 100,
                    'messages': [
                        {
                            'role': 'user',
                            'content': validation_prompt
                        }
                    ]
                }
                
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['content'][0]['text'].strip()
                        
                        try:
                            # Извлекаем число оценки из ответа
                            import re
                            
                            # Ищем числовую оценку в тексте
                            number_pattern = r'(\d+(?:[.,]\d+)?)'
                            matches = re.findall(number_pattern, content)
                            
                            if matches:
                                # Берем первое найденное число
                                score_text = matches[0].replace(',', '.')
                                score = float(score_text)
                                
                                # Ограничиваем диапазон 1-10
                                score = max(1.0, min(10.0, score))
                            else:
                                # Если число не найдено, используем дефолтное значение
                                logger.warning("⚠️ Не найдено числовой оценки в ответе Claude")
                                score = 7.0
                            
                            logger.info(f"✅ Claude валидация завершена: оценка {score}/10")
                            
                            return {
                                'score': score,
                                'is_valid': score >= 7.0,
                                'confidence': 0.9,
                                'issues': [],
                                'suggestions': []
                            }
                            
                        except Exception as e:
                            logger.warning("⚠️ Ошибка парсинга оценки Claude: %s", str(e))
                            logger.warning("Ответ Claude: %s", content[:200])
                            # Возвращаем дефолтную оценку при ошибке
                            return {
                                'score': 7.0,
                                'is_valid': True,
                                'confidence': 0.5,
                                'issues': [f"Ошибка парсинга: {str(e)}"],
                                'suggestions': []
                            }
                    else:
                        logger.warning("⚠️ Claude API ошибка: %s", response.status)
                        
        except Exception as e:
            logger.warning("⚠️ Ошибка Claude валидации: %s", str(e))
        
        # Возвращаем дефолтный результат при ошибке
        return {
            'score': 5.0,
            'is_valid': False,
            'issues': ['Ошибка API валидации'],
            'suggestions': [],
            'confidence': 0.0
        }
    
    async def fix_text_with_claude(self, text: str, target_score: float = 10.0, current_score: float = 5.0) -> str:
        """Исправление текста через Claude"""
        if not self.api_key:
            return text
        
        fix_prompt = f"""
ИСПРАВЬ следующий текст ДО ДОСТИЖЕНИЯ ОЦЕНКИ 10.0/10 согласно ВСЕМ строгим требованиям из промптов.

ТЕКУЩАЯ ОЦЕНКА: {current_score}/10
ЦЕЛЬ: ТОЧНО 10.0/10

ТЕКСТ ДЛЯ ИСПРАВЛЕНИЯ:
{text}

СТРОГИЕ ТРЕБОВАНИЯ ИЗ ПРОМПТА (КАЖДОЕ НАРУШЕНИЕ СНИЖАЕТ ОЦЕНКУ):

🚨 КРИТИЧЕСКИЕ ОШИБКИ ФОРМАТИРОВАНИЯ (исправь ОБЯЗАТЕЛЬНО):
- УДАЛИ ВСЕ HTML-теги: <p>, <h1>, <h2>, <h3>, <h4>, <b>, <i>, <ul>, <li>, <hr>, <div>
- УДАЛИ ВСЕ Markdown: **, __, ##, ###, ---, ***
- ЗАМЕНИ обычные маркеры (*, -, •) на графические иконки: ⭐ 🎯 💫 ⚡ 🔥 💎 🚀 ⚠️ 💰
- ИСПОЛЬЗУЙ правильные заголовки: "🌟 Название раздела"

🚨 СТРУКТУРНЫЕ ТРЕБОВАНИЯ (БЕЗ ИСКЛЮЧЕНИЙ):
ОБЯЗАТЕЛЬНО включи ВСЕ 6 БЛОКОВ В ПРАВИЛЬНОМ ПОРЯДКЕ:

🌟 БЛОК 1 - ВЛИЯНИЕ ЗНАКА ЗОДИАКА НА СУДЬБУ КОМПАНИИ
Минимум 300 слов: поэтичное описание космической природы знака, как знак определяет характер и судьбу компании, глубокие астрологические метафоры

🔮 БЛОК 2 - ВЛИЯНИЕ ПЛАНЕТ И МЕСТА РЕГИСТРАЦИИ  
Минимум 250 слов: влияние планеты-управителя на бизнес, астрологическое значение места регистрации, планетарные аспекты

💎 БЛОК 3 - СИЛЬНЫЕ СТОРОНЫ И ПОТЕНЦИАЛ РОСТА
Минимум 300 слов: объективное описание сильных сторон знака, слабые стороны и способы их преодоления, конкретные возможности роста

🧘 БЛОК 4 - ФИЛОСОФСКАЯ КОНЦЕПЦИЯ КОМПАНИИ
Минимум 250 слов: философская концепция на основе знака зодиака, связь с выбранной сферой деятельности, духовные аспекты

⚠️ БЛОК 5 - ПОТЕНЦИАЛЬНЫЕ РИСКИ И ВЫЗОВЫ
Минимум 200 слов: ОБЯЗАТЕЛЬНО процитируй конкретные новости из контекста, объясни их астрологическое значение

💼 БЛОК 6 - БИЗНЕС-РЕКОМЕНДАЦИИ И СТРАТЕГИИ  
Минимум 200 слов: практические советы, примеры 2-3 известных компаний с тем же знаком

🚨 СОДЕРЖАТЕЛЬНЫЕ ТРЕБОВАНИЯ:
- ОБЯЗАТЕЛЬНО укажи конкретные новости и их влияние на компанию
- ОБЯЗАТЕЛЬНО включи примеры 2-3 известных компаний с тем же знаком  
- НЕ упоминай источники данных (newsdata, prokerala, gemini, openai, api)
- Используй поэтичные астрологические метафоры
- Минимум 1500 слов общего развернутого текста

🚨 ЯЗЫКОВЫЕ ТРЕБОВАНИЯ:
- ТОЛЬКО русский язык
- Профессиональный, уверенный тон
- От эзотерики к бизнес-логике

КРИТИЧЕСКИ ВАЖНО: 
- НЕ СОКРАЩАЙ текст - только ДОПОЛНЯЙ и УЛУЧШАЙ
- КАЖДОЕ требование промпта должно быть ТОЧНО соблюдено
- Стремись к СОВЕРШЕНСТВУ - оценка должна быть 10.0/10

ВЕРНИ ТОЛЬКО ИСПРАВЛЕННЫЙ ТЕКСТ БЕЗ КОММЕНТАРИЕВ.

Верни ТОЛЬКО исправленный текст без комментариев.
"""
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'x-api-key': self.api_key,
                    'content-type': 'application/json',
                    'anthropic-version': '2023-06-01'
                }
                
                payload = {
                    'model': self.model,
                    'max_tokens': self.max_tokens,
                    'messages': [
                        {
                            'role': 'user',
                            'content': fix_prompt
                        }
                    ]
                }
                
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        fixed_text = result['content'][0]['text'].strip()
                        logger.info("✅ Текст исправлен через Claude")
                        return fixed_text
                    else:
                        logger.warning("⚠️ Claude исправление недоступно: %s", response.status)
                        
        except Exception as e:
            logger.warning("⚠️ Ошибка исправления через Claude: %s", str(e))
        
        return text
    
    async def iterative_refinement(self, text: str, original_prompt: str, 
                                 analysis_type: str = "zodiac", 
                                 target_score: float = 10.0,
                                 max_iterations: int = 7,
                                 update_callback=None) -> Tuple[str, float]:
        """
        Итеративное улучшение текста до достижения целевой оценки
        """
        current_text = text
        iteration = 0
        
        logger.info(f"🎯 НАЧИНАЕМ ИТЕРАТИВНОЕ УЛУЧШЕНИЕ ДО ОЦЕНКИ {target_score}/10")
        logger.info("📊 ОСНОВНОЙ АГЕНТ БУДЕТ СТРЕМИТЬСЯ К МАКСИМАЛЬНОЙ ОЦЕНКЕ")
        
        while iteration < max_iterations:
            iteration += 1
            logger.info("=" * 60)
            logger.info(f"🔄 ИТЕРАЦИЯ УЛУЧШЕНИЯ #{iteration} из {max_iterations}")
            logger.info(f"🎯 ЦЕЛЬ: достичь оценки {target_score}/10")
            
            # Получаем оценку от Claude
            validation_result = await self.validate_and_score(current_text, original_prompt, analysis_type)
            current_score = validation_result.get('score', 5.0)
            
            # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ОЦЕНКИ
            logger.info(f"📊 ТЕКУЩАЯ ОЦЕНКА: {current_score}/10")
            
            # Отправляем обновление пользователю если есть callback
            if update_callback:
                try:
                    await update_callback(f"🔍 **Улучшение качества текста...**\n\n"
                                        f"⏳ Итерация {iteration}/{max_iterations}\n"
                                        f"🔄 Обрабатываем...")
                except:
                    pass  # Игнорируем ошибки обновления UI
            
            # ПРОВЕРЯЕМ ДОСТИЖЕНИЕ ЦЕЛИ
            if current_score >= target_score:
                logger.info(f"🎉 ЦЕЛЬ ДОСТИГНУТА! Оценка {current_score}/10 за {iteration} итераций")
                logger.info("🏆 ОСНОВНОЙ АГЕНТ УСПЕШНО ДОСТИГ МАКСИМАЛЬНОГО КАЧЕСТВА!")
                return current_text, current_score
            elif current_score >= 7.0:
                logger.info(f"✅ Минимальный порог пройден: {current_score}/10, но продолжаем к цели {target_score}")
            else:
                logger.warning(f"⚠️ Оценка {current_score}/10 ниже минимума 7.0 - ОСНОВНОЙ АГЕНТ ДОЛЖЕН УЛУЧШИТЬ ТЕКСТ")
            
            # УЛУЧШАЕМ ТЕКСТ
            logger.info("🔧 ОСНОВНОЙ АГЕНТ ПРИМЕНЯЕТ УЛУЧШЕНИЯ...")
            improved_text = await self.fix_text_with_claude(current_text, target_score, current_score)
            
            if improved_text and len(improved_text.strip()) > 100:
                if len(improved_text) < len(current_text) * 0.7:
                    logger.warning(f"⚠️ Текст сократился с {len(current_text)} до {len(improved_text)} символов - отклоняем")
                    break
                
                current_text = improved_text
                logger.info(f"✅ ОСНОВНОЙ АГЕНТ УЛУЧШИЛ ТЕКСТ ({len(current_text)} символов)")
                logger.info(f"🔄 ПЕРЕХОДИМ К СЛЕДУЮЩЕЙ ИТЕРАЦИИ ДЛЯ ДОСТИЖЕНИЯ ЦЕЛИ {target_score}/10")
            else:
                logger.warning("⚠️ ОСНОВНОЙ АГЕНТ НЕ СМОГ УЛУЧШИТЬ ТЕКСТ - завершаем итерации")
                break
        
        logger.warning(f"⚠️ ДОСТИГНУТО МАКСИМУМ ИТЕРАЦИЙ ({max_iterations})")
        logger.info("🔍 ФИНАЛЬНАЯ ПРОВЕРКА КАЧЕСТВА...")
        final_result = await self.validate_and_score(current_text, original_prompt, analysis_type)
        final_score = final_result.get('score', 5.0)
        
        logger.info("=" * 60)
        logger.info("🏁 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
        logger.info(f"📊 ФИНАЛЬНАЯ ОЦЕНКА: {final_score}/10")
        if final_score >= target_score:
            logger.info(f"🎉 ОСНОВНОЙ АГЕНТ ДОСТИГ ЦЕЛИ {target_score}/10!")
        elif final_score >= 7.0:
            logger.info(f"✅ Минимальный порог пройден, но цель {target_score} не достигнута")
        else:
            logger.warning(f"❌ Оценка {final_score} ниже минимума 7.0")
        logger.info("=" * 60)
        
        return current_text, final_score


class AnthropicValidationAgent:
    """Главный класс валидации на Claude"""
    
    def __init__(self):
        """Инициализация агента"""
        self.claude_validator = ClaudeValidatorAgent()
        logger.info("✅ Anthropic валидатор инициализирован")
    
    async def validate_and_fix(self, text: str, analysis_type: str = "zodiac", original_prompt: str = "") -> str:
        """
        Основной метод валидации и исправления
        """
        try:
            # СТРЕМИМСЯ К МАКСИМАЛЬНОЙ ОЦЕНКЕ 10 БАЛЛОВ
            target_score = 10.0
            
            # Запускаем итеративное улучшение с максимальным количеством попыток
            improved_text, final_score = await self.claude_validator.iterative_refinement(
                text=text,
                original_prompt=original_prompt,
                analysis_type=analysis_type,
                target_score=target_score,
                max_iterations=7
            )
            
            logger.info("🎯 Финальная оценка: %s/10 для %s", str(final_score), analysis_type)
            return improved_text
            
        except Exception as e:
            logger.error("❌ Ошибка Claude валидации: %s", str(e))
            return text  # Возвращаем оригинал при ошибке


