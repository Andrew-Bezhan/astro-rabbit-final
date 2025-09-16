# 🔮 AI Astrology Telegram Bot - Replit Setup Complete

## Project Overview
A sophisticated AI-powered Telegram bot that provides astrology consulting for businesses. The bot uses OpenAI's GPT models to analyze company registration data, birth dates of leadership, and provide personalized business forecasts and compatibility analysis.

## Recent Changes (September 16, 2025)
- ✅ Successfully imported and configured for Replit environment
- ✅ Installed Python 3.11 and all required dependencies
- ✅ Set up PostgreSQL database with automatic table creation
- ✅ Configured secure API key management through Replit Secrets
- ✅ Fixed security issue: Database credentials are now masked in logs
- ✅ Enhanced error handling for optional services (NewsData.io, Qdrant)
- ✅ Bot is running and ready to accept user interactions

## Project Architecture

### Core Components
- **Main Bot**: `main.py` - Entry point and bot orchestration
- **Database**: PostgreSQL with SQLAlchemy ORM models for users, companies, and analyses
- **AI Services**: OpenAI-powered astrology agent with specialized prompts
- **API Integrations**: Telegram Bot API, OpenAI API, optional NewsData.io and Qdrant
- **Security**: Environment variables managed through Replit Secrets

### Key Features
1. **Company Zodiac Analysis** - Determine zodiac sign based on registration date
2. **Business Forecasting** - AI-powered predictions using company and leadership data
3. **Compatibility Analysis** - Check compatibility between companies, employees, partners
4. **Daily Forecasts** - Automated daily business insights
5. **Numerology Integration** - Company name analysis and numeric interpretations

## Current Configuration

### ✅ Working Services
- **Telegram Bot**: Fully operational with @Astro_Corp_bot
- **OpenAI Integration**: GPT-4 powered astrology analysis
- **PostgreSQL Database**: Connected and initialized with all tables
- **User Management**: Registration and session handling
- **Core Astrology Features**: All main bot functions operational

### ⚠️ Optional Services (Currently Disabled)
- **NewsData.io**: News analysis for business forecasts (requires API key)
- **Qdrant Vector DB**: Embedding storage for enhanced analysis (requires API key)
- **Advanced Analytics**: Some premium features depend on optional services

## User Preferences
- Language: Russian (bot interface and responses)
- Timezone: UTC for all scheduling and data storage
- Database: PostgreSQL (production-ready with automatic backups)
- Logging: Comprehensive logging with security-conscious credential masking

## Development Notes

### Security Enhancements
- Database connection strings mask passwords in logs
- API keys stored securely in Replit Secrets
- No credentials exposed in code or logs

### Error Handling
- Graceful degradation when optional services unavailable
- Clear user messaging about feature availability
- Robust exception handling prevents crashes

### Future Improvements
1. Add NewsData.io API key for enhanced news analysis
2. Set up Qdrant vector database for improved semantic search
3. Add more astrology calculation providers
4. Implement advanced analytics dashboards

## Running the Bot
The bot runs automatically via the "Telegram Bot" workflow. Users can interact with it directly through Telegram at @Astro_Corp_bot.

## Deployment Status
- ✅ Development Environment: Fully configured and running
- 🔄 Production Deployment: Ready for configuration (use deploy tool when needed)