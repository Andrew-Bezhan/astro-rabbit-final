"""
Агент-валидатор для проверки соответствия генерируемого текста промптам
"""

import re
import json
import traceback
from typing import Dict, Any, List, Tuple, Optional
from utils.logger import setup_logger

logger = setup_logger()

# --- BEGIN SAFE LOGGING HELPERS ---
def _safe_json(obj) -> str:
    """Безопасно сериализует любой объект для лога, не роняя логгер."""
    try:
        if isinstance(obj, str):
            # попытка вытащить JSON из «грязной» строки и красиво отформатировать
            obj_str = obj.strip()
            if obj_str.startswith("{") and obj_str.endswith("}"):
                return json.dumps(json.loads(obj_str), ensure_ascii=False, indent=2)
            return obj
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        try:
            return str(obj)
        except Exception:
            return "<unprintable>"

def log_kv(level: str, msg: str, payload=None):
    """Лог с безопасной подстановкой. Никаких f-строк/format/%."""
    safe_payload = _safe_json(payload)
    if level == "error":
        logger.error(msg + " | data=" + safe_payload)
    elif level == "warning":
        logger.warning(msg + " | data=" + safe_payload)
    elif level == "info":
        logger.info(msg + " | data=" + safe_payload)
    else:
        logger.debug(msg + " | data=" + safe_payload)
# --- END SAFE LOGGING HELPERS ---


class PromptValidator:
    """Валидатор соответствия промптам"""
    
    def __init__(self):
        """Инициализация валидатора"""
        self.validation_rules = {
            'no_html_tags': self._check_no_html_tags,
            'no_markdown': self._check_no_markdown,
            'has_emojis': self._check_has_emojis,
            'proper_structure': self._check_proper_structure,
            'no_hash_symbols': self._check_no_hash_symbols,
            'required_emoji_sections': self._check_required_emoji_sections,
            'graphic_icons_not_bullets': self._check_graphic_icons_not_bullets,
            'astro_symbols_usage': self._check_astro_symbols_usage,
            'russian_language': self._check_russian_language,
            'no_source_mentions': self._check_no_source_mentions,
            'professional_tone': self._check_professional_tone,
            'no_direct_financial_advice': self._check_no_direct_financial_advice,
            'news_context_usage': self._check_news_context_usage,
            'company_examples': self._check_company_examples
        }
    
    def validate_text(self, text: str, analysis_type: str = "zodiac") -> Tuple[bool, List[str]]:
        """
        СТРОГАЯ проверка текста на соответствие промптам с детальным анализом
        
        Args:
            text (str): Текст для проверки
            analysis_type (str): Тип анализа
            
        Returns:
            Tuple[bool, List[str]]: (валиден ли текст, список ошибок с количественной оценкой)
        """
        errors = []
        score = 10.0  # Начальная оценка
        
        # Подробная проверка каждого правила с вычетом баллов
        for rule_name, rule_func in self.validation_rules.items():
            try:
                is_valid, error_msg = rule_func(text)
                if not is_valid:
                    # Вычитаем баллы за нарушения
                    penalty = self._get_penalty_for_rule(rule_name)
                    score -= penalty
                    errors.append(f"{rule_name} (-{penalty} баллов): {error_msg}")
            except Exception as e:
                score -= 1.0
                errors.append(f"{rule_name} (ошибка проверки, -1 балл): {e}")
        
        # Обеспечиваем минимальную оценку 1.0
        score = max(1.0, score)
        is_valid = score >= 7.0  # Минимальный порог для валидности
        
        if not is_valid:
            logger.warning("⚠️ ОСНОВНОЙ АГЕНТ НЕ СОБЛЮДАЕТ ПРОМПТ (%s): Оценка %.1f/10", analysis_type, score)
            logger.warning("📋 Список нарушений: %s", errors[:5])  # Показываем первые 5 ошибок
        else:
            logger.info("✅ Текст соответствует промпту (%s): Оценка %.1f/10", analysis_type, score)
        
        return is_valid, errors
    
    def _get_penalty_for_rule(self, rule_name: str) -> float:
        """Получить штраф в баллах за нарушение правила"""
        penalty_map = {
            'no_html_tags': 3.0,              # Критично для Telegram
            'no_markdown': 3.0,               # Критично для Telegram  
            'required_emoji_sections': 3.0,   # Критично - основные блоки из промпта
            'news_context_usage': 2.5,        # Критично - требование промпта
            'company_examples': 2.0,          # Критично - требование промпта
            'no_hash_symbols': 2.0,           # Критично для Telegram
            'graphic_icons_not_bullets': 2.0, # Важно для оформления
            'proper_structure': 2.0,          # Важно для читаемости
            'russian_language': 2.0,          # Важно для целевой аудитории
            'has_emojis': 1.5,               # Важно для оформления
            'no_source_mentions': 1.5,        # Профессионализм
            'astro_symbols_usage': 1.0,       # Дополнительно
            'professional_tone': 1.0,         # Стиль
            'no_direct_financial_advice': 1.0  # Юридические требования
        }
        return penalty_map.get(rule_name, 1.0)
    
    def _check_no_html_tags(self, text: str) -> Tuple[bool, str]:
        """СТРОГАЯ проверка отсутствия HTML-тегов (КРИТИЧНО для Telegram)"""
        # Запрещенные HTML теги (включая <b> и <i> - используем только простой текст)
        forbidden_tags = re.findall(r'<[^>]+>', text)
        if forbidden_tags:
            unique_tags = list(set(forbidden_tags))
            return False, f"КРИТИЧНО: Найдены HTML-теги: {unique_tags[:10]} (всего: {len(forbidden_tags)})"
        return True, ""
    
    def _check_no_markdown(self, text: str) -> Tuple[bool, str]:
        """СТРОГАЯ проверка отсутствия Markdown (КРИТИЧНО для Telegram)"""
        markdown_violations = []
        
        # Паттерны Markdown
        markdown_patterns = [
            (r'\*\*[^*]+\*\*', '**жирный**'),      # **жирный**
            (r'__[^_]+__', '__жирный__'),          # __жирный__
            (r'\*[^*\s]+[^*]*\*', '*курсив*'),     # *курсив*
            (r'_[^_\s]+[^_]*_', '_курсив_'),       # _курсив_
            (r'^#{1,6}\s', '# заголовки'),         # # заголовки
            (r'^---+', '--- разделители'),         # --- разделители
            (r'^\*\s', '* списки'),               # * списки  
            (r'^-\s', '- списки'),                # - списки
            (r'^\+\s', '+ списки'),               # + списки
        ]
        
        for pattern, description in markdown_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            if matches:
                markdown_violations.extend([f"{description}: {m[:50]}..." for m in matches[:3]])
        
        if markdown_violations:
            return False, f"КРИТИЧНО: Найден Markdown: {markdown_violations[:5]}"
        
        return True, ""
    
    def _check_has_emojis(self, text: str) -> Tuple[bool, str]:
        """Проверка наличия эмодзи"""
        emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF]'
        emojis = re.findall(emoji_pattern, text)
        
        if len(emojis) < 5:
            return False, f"Недостаточно эмодзи: {len(emojis)} (нужно минимум 5)"
        
        return True, ""
    
    def _check_proper_structure(self, text: str) -> Tuple[bool, str]:
        """Проверка правильной структуры"""
        # Проверяем наличие разделов с эмодзи
        required_sections = ['🌟', '💎', '🚀', '⚠️']
        found_sections = []
        
        for section in required_sections:
            if section in text:
                found_sections.append(section)
        
        if len(found_sections) < 3:
            return False, f"Недостаточно разделов: {found_sections} (нужно минимум 3 из {required_sections})"
        
        return True, ""
    
    def _check_no_hash_symbols(self, text: str) -> Tuple[bool, str]:
        """Проверка отсутствия символов #"""
        if '#' in text:
            hash_lines = [line.strip() for line in text.split('\n') if '#' in line]
            return False, f"Найдены символы #: {hash_lines[:3]}"
        
        return True, ""
    
    def _check_required_emoji_sections(self, text: str) -> Tuple[bool, str]:
        """СТРОГАЯ проверка наличия обязательных 6 блоков из prompts.py"""
        # Обязательные блоки ТОЧНО как указано в COMPANY_ZODIAC_PROMPT
        required_blocks = [
            ('🌟', 'ВЛИЯНИЕ ЗНАКА ЗОДИАКА НА СУДЬБУ', 300),
            ('🔮', 'ВЛИЯНИЕ ПЛАНЕТ И МЕСТА РЕГИСТРАЦИИ', 250),
            ('💎', 'СИЛЬНЫЕ СТОРОНЫ И ПОТЕНЦИАЛ РОСТА', 300),
            ('🧘', 'ФИЛОСОФСКАЯ КОНЦЕПЦИЯ КОМПАНИИ', 250),
            ('⚠️', 'ПОТЕНЦИАЛЬНЫЕ РИСКИ И ВЫЗОВЫ', 200),
            ('💼', 'БИЗНЕС-РЕКОМЕНДАЦИИ И СТРАТЕГИИ', 200)
        ]
        
        missing_blocks = []
        insufficient_blocks = []
        
        for emoji, block_name, min_words in required_blocks:
            # Проверяем наличие эмодзи в заголовке блока
            block_pattern = rf'{re.escape(emoji)}\s+[^\\n]*{re.escape(block_name.split()[0])}'
            block_match = re.search(block_pattern, text, re.IGNORECASE)
            
            if not block_match:
                # Проверяем просто наличие эмодзи
                if emoji not in text:
                    missing_blocks.append(f"{emoji} {block_name}")
                else:
                    missing_blocks.append(f"{emoji} {block_name} (неправильный заголовок)")
            else:
                # Проверяем объем блока (примерная проверка)
                # Находим начало и конец блока
                start_pos = block_match.end()
                # Ищем следующий блок или конец текста
                next_block_pattern = r'🌟|🔮|💎|🧘|⚠️|💼'
                next_match = re.search(next_block_pattern, text[start_pos:])
                
                if next_match:
                    block_text = text[start_pos:start_pos + next_match.start()]
                else:
                    block_text = text[start_pos:]
                
                word_count = len(block_text.split())
                if word_count < min_words * 0.7:  # Допускаем 30% отклонение
                    insufficient_blocks.append(f"{emoji} {block_name} ({word_count} слов, нужно {min_words}+)")
        
        # Проверяем общий объем
        total_words = len(text.split())
        errors = []
        
        if missing_blocks:
            errors.append(f"Отсутствуют блоки: {missing_blocks}")
        
        if insufficient_blocks:
            errors.append(f"Недостаточный объем блоков: {insufficient_blocks}")
            
        if total_words < 1200:  # Минимум для качественного анализа
            errors.append(f"Общий объем {total_words} слов недостаточен (нужно 1500+ слов)")
        
        # Проверяем правильный порядок блоков
        emoji_order = ['🌟', '🔮', '💎', '🧘', '⚠️', '💼']
        found_positions = []
        
        for emoji in emoji_order:
            pos = text.find(emoji)
            if pos != -1:
                found_positions.append((emoji, pos))
        
        # Проверяем, что найденные блоки идут в правильном порядке
        if len(found_positions) > 1:
            sorted_positions = sorted(found_positions, key=lambda x: x[1])
            expected_order = [emoji for emoji, _ in sorted_positions]
            actual_order = [emoji for emoji in emoji_order if emoji in expected_order]
            
            if expected_order != actual_order:
                errors.append(f"Неправильный порядок блоков: найдено {expected_order}, ожидается {actual_order}")
        
        if errors:
            return False, f"КРИТИЧНО - структура промпта нарушена: {'; '.join(errors[:3])}"
        
        return True, ""
    
    def _check_russian_language(self, text: str) -> Tuple[bool, str]:
        """Проверка использования русского языка"""
        # Простая проверка наличия кириллицы
        cyrillic_chars = len(re.findall(r'[а-яё]', text.lower()))
        total_letters = len(re.findall(r'[a-zA-Zа-яёА-ЯЁ]', text))
        
        if total_letters > 0:
            cyrillic_ratio = cyrillic_chars / total_letters
            if cyrillic_ratio < 0.8:
                return False, f"Недостаточно русского текста: {cyrillic_ratio:.2%} кириллицы"
        
        return True, ""
    
    def _check_no_source_mentions(self, text: str) -> Tuple[bool, str]:
        """Проверка отсутствия упоминания источников"""
        source_keywords = [
            'источник', 'данные получены', 'согласно', 'по данным',
            'newsdata', 'prokerala', 'gemini', 'openai', 'api'
        ]
        
        text_lower = text.lower()
        found_sources = [word for word in source_keywords if word in text_lower]
        
        if found_sources:
            return False, f"Найдены упоминания источников: {found_sources}"
        
        return True, ""
    
    def _check_graphic_icons_not_bullets(self, text: str) -> Tuple[bool, str]:
        """Проверка использования графических иконок вместо обычных маркеров"""
        # Ищем обычные маркеры
        bullet_patterns = [r'^\s*\*\s', r'^\s*-\s', r'^\s*•\s']
        found_bullets = []
        
        for pattern in bullet_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            if matches:
                found_bullets.extend(matches)
        
        if found_bullets:
            return False, f"Найдены обычные маркеры вместо графических иконок: {found_bullets[:3]}"
        
        # Проверяем наличие графических иконок из prompts.py
        required_icons = ['⭐', '🎯', '💫', '⚡', '🔥', '💎', '🚀', '⚠️', '💰']
        found_icons = [icon for icon in required_icons if icon in text]
        
        if len(found_icons) < 3:
            return False, f"Недостаточно графических иконок. Найдено: {found_icons}, нужно минимум 3 из {required_icons}"
        
        return True, ""
    
    def _check_astro_symbols_usage(self, text: str) -> Tuple[bool, str]:
        """Проверка использования астрологических символов"""
        astro_symbols = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓', '☉', '☽', '☿', '♀', '♂', '♃', '♄', '⛢', '♆', '♇']
        found_symbols = [symbol for symbol in astro_symbols if symbol in text]
        
        if len(found_symbols) < 2:
            return False, f"Недостаточно астрологических символов. Найдено: {found_symbols}, нужно минимум 2"
        
        return True, ""
    
    def _check_professional_tone(self, text: str) -> Tuple[bool, str]:
        """Проверка профессионального тона"""
        # Ищем непрофессиональные фразы
        unprofessional_phrases = [
            'извините', 'простите', 'к сожалению', 'возможно', 'наверное', 'может быть',
            'я думаю', 'я считаю', 'по моему мнению'
        ]
        
        text_lower = text.lower()
        found_unprofessional = [phrase for phrase in unprofessional_phrases if phrase in text_lower]
        
        if found_unprofessional:
            return False, f"Найдены непрофессиональные фразы: {found_unprofessional[:3]}"
        
        return True, ""
    
    def _check_no_direct_financial_advice(self, text: str) -> Tuple[bool, str]:
        """Проверка отсутствия прямых финансовых советов"""
        direct_advice_patterns = [
            r'покупайте\s+акции', r'продавайте\s+акции', r'инвестируйте\s+в',
            r'купите\s+', r'продайте\s+', r'вложите\s+деньги'
        ]
        
        text_lower = text.lower()
        found_advice = []
        
        for pattern in direct_advice_patterns:
            if re.search(pattern, text_lower):
                found_advice.append(pattern)
        
        if found_advice:
            return False, f"Найдены прямые финансовые советы: {found_advice[:2]}"
        
        return True, ""
    
    def _check_news_context_usage(self, text: str) -> Tuple[bool, str]:
        """КРИТИЧНАЯ проверка использования контекста новостей"""
        # Ключевые слова, указывающие на использование новостного контекста
        news_indicators = [
            'согласно последним новостям', 'последние новости', 'текущие события',
            'новости о', 'события в', 'согласно данным', 'по информации',
            'недавние события', 'актуальная ситуация', 'текущая ситуация'
        ]
        
        text_lower = text.lower()
        found_indicators = [indicator for indicator in news_indicators if indicator in text_lower]
        
        if not found_indicators:
            # Проверяем наличие современных терминов, которые могут указывать на новости
            modern_terms = [
                'экономика', 'рынок', 'инфляция', 'санкции', 'кризис', 
                'технологии', 'цифровизация', 'AI', 'искусственный интеллект',
                'ESG', 'устойчивое развитие', 'глобализация'
            ]
            
            found_modern = [term for term in modern_terms if term in text_lower]
            
            if len(found_modern) < 2:
                return False, f"КРИТИЧНО: Отсутствует контекст новостей и современных событий. Найдено индикаторов: {found_indicators}, современных терминов: {found_modern}"
        
        return True, f"Найдены индикаторы новостного контекста: {found_indicators[:3]}"
    
    def _check_company_examples(self, text: str) -> Tuple[bool, str]:
        """КРИТИЧНАЯ проверка наличия примеров известных компаний"""
        # Паттерны для поиска примеров компаний
        company_patterns = [
            r'компани[яи]\s+[А-ЯЁ][а-яё]+',           # компания Apple
            r'бренд\s+[А-ЯЁ][а-яё]+',                # бренд Nike
            r'корпораци[яи]\s+[А-ЯЁ][а-яё]+',        # корпорация Microsoft
            r'гигант\s+[А-ЯЁ][а-яё]+',               # гигант Amazon
            r'[А-ЯЁ][а-яё]+\s+(?:Inc|LLC|Corp|Ltd)', # Apple Inc
            r'известн[ая].*[А-ЯЁ][а-яё]+',           # известная Tesla
        ]
        
        # Известные компании разных знаков зодиака
        famous_companies = [
            'apple', 'microsoft', 'google', 'amazon', 'tesla', 'meta', 'netflix',
            'nike', 'coca-cola', 'mcdonalds', 'starbucks', 'disney', 'bmw',
            'mercedes', 'volkswagen', 'toyota', 'samsung', 'sony', 'lg',
            'alibaba', 'tencent', 'baidu', 'xiaomi', 'huawei',
            'сбербанк', 'газпром', 'лукойл', 'роснефт', 'яндекс', 'мтс'
        ]
        
        text_lower = text.lower()
        found_companies = []
        
        # Поиск прямых упоминаний известных компаний
        for company in famous_companies:
            if company in text_lower:
                found_companies.append(company)
        
        # Поиск паттернов упоминания компаний
        company_mentions = []
        for pattern in company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            company_mentions.extend(matches[:3])  # Не более 3 для каждого паттерна
        
        total_examples = len(found_companies) + len(company_mentions)
        
        if total_examples < 2:
            return False, f"КРИТИЧНО: Недостаточно примеров компаний. Найдено: {found_companies[:3]} + {company_mentions[:3]} (нужно минимум 2-3 примера)"
        
        return True, f"Найдены примеры компаний: {found_companies[:3]} + {company_mentions[:3]}"
    
    def fix_text(self, text: str) -> str:
        """
        Автоматическое исправление текста
        
        Args:
            text (str): Исходный текст
            
        Returns:
            str: Исправленный текст
        """
        # Убираем только запрещенные HTML-теги (сохраняем <b> и <i> для Telegram)
        text = re.sub(r'<(?!/?[bi]>)[^>]+>', '', text)
        
        # Убираем Markdown
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **жирный**
        text = re.sub(r'__([^_]+)__', r'\1', text)      # __жирный__
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *курсив*
        text = re.sub(r'_([^_]+)_', r'\1', text)        # _курсив_
        
        # Убираем символы # и заменяем на эмодзи
        text = re.sub(r'^#{1,6}\s*(.+)$', r'🌟 \1', text, flags=re.MULTILINE)
        text = re.sub(r'###\s*(.+)', r'💎 \1', text)
        text = re.sub(r'##\s*(.+)', r'🚀 \1', text)
        text = re.sub(r'#\s*(.+)', r'⭐ \1', text)
        
        # Заменяем разделители
        text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^===+$', '', text, flags=re.MULTILINE)
        
        # Убираем упоминания источников
        text = re.sub(r'(источник|данные получены|согласно|по данным)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(newsdata|prokerala|gemini|openai|api)', '', text, flags=re.IGNORECASE)
        
        # Заменяем обычные маркеры на графические иконки (только если их еще нет)
        text = re.sub(r'^\s*\*\s+(?!⭐|💫|🎯|⚡|🔥|💎|🚀|⚠️|💰)(.+)', r'⭐ \1', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*-\s+(?!⭐|💫|🎯|⚡|🔥|💎|🚀|⚠️|💰)(.+)', r'💫 \1', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*•\s+(?!⭐|💫|🎯|⚡|🔥|💎|🚀|⚠️|💰)(.+)', r'🎯 \1', text, flags=re.MULTILINE)
        
        # Убираем непрофессиональные фразы
        unprofessional_replacements = {
            'извините': '', 'простите': '', 'к сожалению': '',
            'возможно': 'вероятно', 'наверное': 'скорее всего', 'может быть': 'вероятно',
            'я думаю': '', 'я считаю': '', 'по моему мнению': ''
        }
        
        for phrase, replacement in unprofessional_replacements.items():
            text = re.sub(phrase, replacement, text, flags=re.IGNORECASE)
        
        # Добавляем обязательные 6 блоков если их нет
        if '🌟' not in text or 'ВЛИЯНИЕ ЗНАКА ЗОДИАКА' not in text:
            text = '🌟 ВЛИЯНИЕ ЗНАКА ЗОДИАКА НА СУДЬБУ КОМПАНИИ\n\n' + text
        if '🔮' not in text or 'ВЛИЯНИЕ ПЛАНЕТ' not in text:
            text = text + '\n\n🔮 ВЛИЯНИЕ ПЛАНЕТ И МЕСТА РЕГИСТРАЦИИ'
        if '💎' not in text or 'СИЛЬНЫЕ СТОРОНЫ' not in text:
            text = text + '\n\n💎 СИЛЬНЫЕ СТОРОНЫ И ПОТЕНЦИАЛ РОСТА'
        if '🧘' not in text or 'ФИЛОСОФСКАЯ КОНЦЕПЦИЯ' not in text:
            text = text + '\n\n🧘 ФИЛОСОФСКАЯ КОНЦЕПЦИЯ КОМПАНИИ'
        if '⚠️' not in text or 'ПОТЕНЦИАЛЬНЫЕ РИСКИ' not in text:
            text = text + '\n\n⚠️ ПОТЕНЦИАЛЬНЫЕ РИСКИ И ВЫЗОВЫ'
        if '💼' not in text or 'БИЗНЕС-РЕКОМЕНДАЦИИ' not in text:
            text = text + '\n\n💼 БИЗНЕС-РЕКОМЕНДАЦИИ И СТРАТЕГИИ'
        
        # Добавляем пустые строки между разделами с эмодзи
        text = re.sub(r'(\n)(🌟|💎|🚀|⚠️|📈|🔮|💼|🎯|💡|✨)', r'\1\n\2', text)
        
        # Убираем лишние переносы
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text.strip()


class ValidationAgent:
    """Агент для валидации и исправления промптов с RLHF"""
    
    def __init__(self):
        """Инициализация агента валидации"""
        # Используем Anthropic валидатор как основной
        try:
            from validation_agent.claude_validator import AnthropicValidationAgent
            self.claude_agent = AnthropicValidationAgent()
            self.use_claude = True
            logger.info("✅ Anthropic валидатор инициализирован")
        except Exception as e:
            logger.warning("⚠️ Anthropic валидатор недоступен: %s", str(e))
            # Резервный локальный валидатор
            self.validator = PromptValidator()
            self.use_claude = False
            logger.info("✅ Резервный валидатор инициализирован")
    
    async def validate_and_fix(self, text: str, analysis_type: str = "zodiac", original_prompt: str = "") -> str:
        """
        Валидация и исправление текста до достижения минимум 7 баллов
        
        Args:
            text (str): Исходный текст
            analysis_type (str): Тип анализа
            original_prompt (str): Оригинальный промпт для валидации
            
        Returns:
            str: Валидированный и исправленный текст
        """
        try:
            if self.use_claude and hasattr(self, 'claude_agent'):
                # Используем Anthropic валидатор как основной
                logger.info("🤖 Используем Anthropic валидатор для %s (цель: 7+ баллов)", analysis_type)
                
                # СТРЕМИМСЯ К МАКСИМАЛЬНОЙ ОЦЕНКЕ 10 БАЛЛОВ
                logger.info("🎯 ЦЕЛЬ: достичь оценки 10.0/10 (стремимся к совершенству)")
                
                # Запускаем валидацию через Claude с итеративным улучшением
                improved_text = await self.claude_agent.validate_and_fix(
                    text=text,
                    analysis_type=analysis_type,
                    original_prompt=original_prompt
                )
                
                # Получаем финальную оценку
                final_result = await self.claude_agent.claude_validator.validate_and_score(
                    improved_text, original_prompt, analysis_type
                )
                final_score = final_result.get('score', 7.0)
                logger.info("🏆 Anthropic валидация завершена: %.1f/10", final_score)
                return improved_text
            else:
                # Используем резервный валидатор
                logger.info("🔧 Используем резервный валидатор для %s", analysis_type)
                return await self._fallback_validation(text, analysis_type, original_prompt)
                
        except Exception as e:
            logger.error("❌ Критическая ошибка валидации: %s", str(e))
            logger.error("Stacktrace: %s", traceback.format_exc())
            # ВСЕГДА возвращаем хотя бы базовую очистку
            return self._basic_cleanup(text)
    
    def _basic_cleanup(self, text: str) -> str:
        """Базовая очистка текста при ошибках валидации"""
        if not text:
            return "Анализ недоступен"
        
        # Минимальная обработка для читаемости
        text = re.sub(r'<(?!/?[bi]>)[^>]+>', '', text)  # Убираем лишние HTML
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Нормализуем переносы
        
        return text.strip()
    
    async def _fallback_validation(self, text: str, analysis_type: str, original_prompt: str) -> str:
        """Резервная валидация при недоступности Claude"""
        import asyncio
        
        if not hasattr(self, 'validator'):
            self.validator = PromptValidator()
        
        current_text = text
        max_iterations = 2  # Уменьшаем для резервного режима
        iteration = 0
        
        logger.info("🔍 Резервная валидация текста типа '%s'", analysis_type)
        
        while iteration < max_iterations:
            iteration += 1
            logger.info("🔄 Итерация валидации #%d", iteration)
            
            # Локальная валидация
            is_valid_local, local_errors = self.validator.validate_text(current_text, analysis_type)
            
            if is_valid_local:
                logger.info("✅ Резервная валидация завершена за %d итераций", iteration)
                return current_text
            
            # Исправляем локально
            current_text = self.validator.fix_text(current_text)
            logger.info("🔧 Текст исправлен локально (итерация %d)", iteration)
            
            # Пауза между итерациями
            if iteration < max_iterations:
                await asyncio.sleep(0.1)
        
        return current_text
    
    async def validate_and_fix_with_feedback(self, 
                                           text: str, 
                                           analysis_type: str = "zodiac", 
                                           original_prompt: str = "",
                                           generation_function=None,
                                           generation_params: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Валидация с детальной обратной связью для основного агента
        
        Args:
            text (str): Исходный текст
            analysis_type (str): Тип анализа
            original_prompt (str): Оригинальный промпт
            generation_function: Функция для регенерации (опционально)
            generation_params (Dict): Параметры генерации (опционально)
            
        Returns:
            Tuple[str, Dict]: (улучшенный текст, детальные метрики)
        """
        logger.info("🔧 ЗАПУСК ВАЛИДАЦИИ С ОБРАТНОЙ СВЯЗЬЮ ДЛЯ ОСНОВНОГО АГЕНТА")
        
        # Получаем детальную оценку
        is_valid, error_list = self.validate_text(text, analysis_type)
        score = max(1.0, 10.0 - sum([self._get_penalty_for_rule(err.split(' ')[0]) for err in error_list]))
        
        # Создаем детальный отчет для основного агента
        feedback_report = {
            'current_score': round(score, 1),
            'is_valid': is_valid,
            'target_score': 10.0,
            'critical_errors': [err for err in error_list if any(rule in err for rule in 
                               ['no_html_tags', 'no_markdown', 'required_emoji_sections', 'news_context_usage'])],
            'moderate_errors': [err for err in error_list if err not in [err for err in error_list if any(rule in err for rule in 
                               ['no_html_tags', 'no_markdown', 'required_emoji_sections', 'news_context_usage'])]],
            'missing_requirements': self._identify_missing_requirements(text),
            'formatting_issues': self._identify_formatting_issues(text),
            'content_gaps': self._identify_content_gaps(text),
        }
        
        logger.info("📊 ОТЧЕТ ДЛЯ ОСНОВНОГО АГЕНТА:")
        logger.info("🎯 Текущая оценка: %.1f/10 (цель: 10.0)", score)
        logger.info("� Критичные ошибки: %d", len(feedback_report['critical_errors']))
        logger.info("⚠️ Умеренные ошибки: %d", len(feedback_report['moderate_errors']))
        
        if score >= 10.0:
            logger.info("🎉 ОСНОВНОЙ АГЕНТ ДОСТИГ СОВЕРШЕНСТВА!")
            return text, feedback_report
        elif score >= 7.0:
            logger.info("✅ Основной агент достиг минимального порога, но может улучшить до 10.0")
        else:
            logger.warning("❌ ОСНОВНОЙ АГЕНТ ДОЛЖЕН КРИТИЧЕСКИ УЛУЧШИТЬ РАБОТУ")
        
        # Если есть функция регенерации, используем её с обратной связью
        if generation_function and generation_params and score < 8.0:
            logger.info("🔄 ЗАПРАШИВАЕМ РЕГЕНЕРАЦИЮ У ОСНОВНОГО АГЕНТА С УЧЕТОМ ОШИБОК")
            
            # Добавляем информацию об ошибках в параметры генерации
            enhanced_params = generation_params.copy()
            enhanced_params['validation_feedback'] = feedback_report
            enhanced_params['improvement_instructions'] = self._create_improvement_instructions(feedback_report)
            
            try:
                improved_text = await generation_function(**enhanced_params)
                if improved_text and len(improved_text.strip()) > 500:
                    # Повторная валидация улучшенного текста
                    is_improved, new_errors = self.validate_text(improved_text, analysis_type)
                    new_score = max(1.0, 10.0 - sum([self._get_penalty_for_rule(err.split(' ')[0]) for err in new_errors]))
                    
                    if new_score > score:
                        logger.info("📈 ОСНОВНОЙ АГЕНТ УЛУЧШИЛ РЕЗУЛЬТАТ: %.1f → %.1f", score, new_score)
                        feedback_report['current_score'] = round(new_score, 1)
                        feedback_report['improvement'] = round(new_score - score, 1)
                        return improved_text, feedback_report
                    else:
                        logger.warning("📉 Регенерация не улучшила результат: %.1f vs %.1f", new_score, score)
            except Exception as e:
                logger.error("❌ Ошибка регенерации: %s", str(e))
        
        # Применяем локальные исправления
        improved_text = await self.validate_and_fix(text, analysis_type, original_prompt)
        return improved_text, feedback_report
    
    def _identify_missing_requirements(self, text: str) -> List[str]:
        """Определить отсутствующие требования из промпта"""
        missing = []
        
        # Проверка обязательных блоков
        required_emojis = ['🌟', '🔮', '💎', '🧘', '⚠️', '💼']
        for emoji in required_emojis:
            if emoji not in text:
                missing.append(f"Отсутствует блок с эмодзи {emoji}")
        
        # Проверка новостного контекста
        if 'новост' not in text.lower() and 'событ' not in text.lower():
            missing.append("Отсутствует контекст актуальных новостей")
        
        # Проверка примеров компаний
        company_keywords = ['компани', 'корпораци', 'бренд', 'apple', 'microsoft', 'google']
        if not any(keyword in text.lower() for keyword in company_keywords):
            missing.append("Отсутствуют примеры известных компаний")
            
        return missing
    
    def _identify_formatting_issues(self, text: str) -> List[str]:
        """Определить проблемы форматирования"""
        issues = []
        
        # HTML теги
        if re.search(r'<[^>]+>', text):
            issues.append("Обнаружены HTML-теги (запрещены для Telegram)")
        
        # Markdown
        if re.search(r'\*\*[^*]+\*\*|__[^_]+__|^#{1,6}\s', text, re.MULTILINE):
            issues.append("Обнаружен Markdown (запрещен для Telegram)")
        
        # Обычные маркеры
        if re.search(r'^\s*[\*\-•]\s', text, re.MULTILINE):
            issues.append("Используются обычные маркеры вместо графических иконок")
            
        return issues
    
    def _identify_content_gaps(self, text: str) -> List[str]:
        """Определить пробелы в содержании"""
        gaps = []
        
        # Проверка объема
        word_count = len(text.split())
        if word_count < 1500:
            gaps.append(f"Недостаточный объем: {word_count} слов (нужно 1500+)")
        
        # Проверка астрологических символов
        astro_symbols = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']
        if not any(symbol in text for symbol in astro_symbols):
            gaps.append("Отсутствуют астрологические символы")
        
        # Проверка эмодзи
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF]', text))
        if emoji_count < 10:
            gaps.append(f"Недостаточно эмодзи: {emoji_count} (нужно 10+)")
            
        return gaps
    
    def _create_improvement_instructions(self, feedback: Dict[str, Any]) -> str:
        """Создать инструкции по улучшению для основного агента"""
        instructions = []
        
        instructions.append(f"ТЕКУЩАЯ ОЦЕНКА: {feedback['current_score']}/10")
        instructions.append(f"ЦЕЛЬ: ДОСТИЧЬ 10.0/10 БАЛЛОВ")
        
        if feedback['critical_errors']:
            instructions.append("🚨 КРИТИЧНЫЕ ОШИБКИ (исправь ОБЯЗАТЕЛЬНО):")
            for error in feedback['critical_errors'][:5]:
                instructions.append(f"  - {error}")
        
        if feedback['missing_requirements']:
            instructions.append("📋 ОТСУТСТВУЮЩИЕ ТРЕБОВАНИЯ:")
            for req in feedback['missing_requirements']:
                instructions.append(f"  - {req}")
        
        if feedback['formatting_issues']:
            instructions.append("🎨 ПРОБЛЕМЫ ФОРМАТИРОВАНИЯ:")
            for issue in feedback['formatting_issues']:
                instructions.append(f"  - {issue}")
        
        instructions.append("💡 КЛЮЧЕВЫЕ ТРЕБОВАНИЯ ДЛЯ ОЦЕНКИ 10/10:")
        instructions.append("  - ВСЕ 6 блоков с правильными эмодзи")
        instructions.append("  - НИКАКИХ HTML-тегов или Markdown")
        instructions.append("  - Примеры 2-3 известных компаний")
        instructions.append("  - Конкретные новости и их влияние")
        instructions.append("  - Минимум 1500 слов качественного контента")
        
        return "\n".join(instructions)
