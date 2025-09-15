# -*- coding: utf-8 -*-
"""
Обработчик для анализа знаков зодиака
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from .base_handler import BaseHandler
from utils.logger import setup_logger
from ai_astrologist.prompts import COMPANY_ZODIAC_INFO_PROMPT
import json
import os

logger = setup_logger()


class ZodiacHandler(BaseHandler):
    """Обработчик для анализа знаков зодиака"""
    
    def __init__(self):
        super().__init__()
    
    async def show_zodiac_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню знаков зодиака"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        
        # Загружаем известные компании по знакам зодиака
        companies_data = await self._load_companies_by_zodiac()
        
        keyboard = []
        for sign, companies in companies_data.items():
            button_text = f"{self._get_zodiac_emoji(sign)} {sign}"
            callback_data = f"zodiac_analysis_{sign}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Добавляем кнопку "Назад"
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "🔮 **Анализ знаков зодиака**\n\n"
            "Выберите знак зодиака для анализа:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def analyze_zodiac_sign(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Анализ конкретного знака зодиака"""
        if not update.callback_query or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        callback_data = update.callback_query.data
        
        # Извлекаем знак зодиака из callback_data
        sign = callback_data.replace("zodiac_analysis_", "")
        
        try:
            # Получаем информацию о компаниях этого знака
            companies_data = await self._load_companies_by_zodiac()
            sign_companies = companies_data.get(sign, [])
            
            # Получаем актуальные новости
            news_data = await self._get_news_data()
            
            # Формируем промпт для анализа
            prompt = COMPANY_ZODIAC_INFO_PROMPT.format(
                zodiac_sign=sign,
                companies=", ".join(sign_companies[:10]),  # Берем первые 10 компаний
                news_context=news_data
            )
            
            # Отправляем сообщение о начале анализа
            await update.callback_query.edit_message_text(
                f"🔮 Анализирую знак **{sign}**...\n\n"
                f"📊 Компании: {len(sign_companies)}\n"
                f"📰 Учитываю актуальные новости",
                parse_mode='Markdown'
            )
            
            # Генерируем анализ через AI
            analysis = await self.astro_agent.generate_analysis(
                prompt=prompt,
                user_id=user_id,
                analysis_type="zodiac_analysis"
            )
            
            if analysis and analysis.get('content'):
                # Валидируем результат
                validation_result = await self._validate_analysis(analysis['content'], "zodiac_analysis")
                
                # Формируем финальное сообщение
                message = f"🔮 **Анализ знака {sign}**\n\n"
                message += analysis['content']
                
                if validation_result['score'] < 7:
                    message += f"\n\n⚠️ *Качество анализа: {validation_result['score']}/10*"
                
                # Добавляем кнопки
                keyboard = [
                    [InlineKeyboardButton("🔄 Новый анализ", callback_data=f"zodiac_analysis_{sign}")],
                    [InlineKeyboardButton("🔙 К знакам зодиака", callback_data="zodiac_menu")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Разбиваем длинное сообщение на части
                await self._send_long_message(
                    update.callback_query, 
                    message, 
                    reply_markup=reply_markup
                )
                
                # Автосохранение
                await self._auto_save_analysis(user_id, analysis, "zodiac_analysis", sign)
                
            else:
                await update.callback_query.edit_message_text(
                    f"❌ Не удалось сгенерировать анализ для знака {sign}.\n"
                    f"Попробуйте еще раз.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"zodiac_analysis_{sign}")
                    ]])
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка анализа знака зодиака {sign}: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Произошла ошибка при анализе знака {sign}.\n"
                f"Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 К знакам зодиака", callback_data="zodiac_menu")
                ]])
            )
    
    async def _load_companies_by_zodiac(self) -> dict:
        """Загрузка компаний по знакам зодиака"""
        try:
            companies_file = "ai_astrologist/known_companies.json"
            if os.path.exists(companies_file):
                with open(companies_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки компаний: {e}")
            return {}
    
    def _get_zodiac_emoji(self, sign: str) -> str:
        """Получить эмодзи для знака зодиака"""
        emoji_map = {
            "Овен": "♈",
            "Телец": "♉", 
            "Близнецы": "♊",
            "Рак": "♋",
            "Лев": "♌",
            "Дева": "♍",
            "Весы": "♎",
            "Скорпион": "♏",
            "Стрелец": "♐",
            "Козерог": "♑",
            "Водолей": "♒",
            "Рыбы": "♓"
        }
        return emoji_map.get(sign, "🔮")
