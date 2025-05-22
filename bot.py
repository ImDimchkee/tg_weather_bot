import os
import logging

from dotenv import load_dotenv

# Telegram api imports
# ref: https://docs.python-telegram-bot.org/
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters

# Open-meteo module import
from open_meteo import geocoding_search_city, scrape_weather_data


# logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger(__name__)


async def start(update: Update) -> None:
    """Awaits for 
    Args:
        update (Update): _description_
    """
    await update.message.reply_text("Hello! This bots let's you query weather conditions in specified location")


async def weather_handler(update: Update):
    """Scrape weather data based on provided user input"""
    city_data = geocoding_search_city(update.message.text.strip())
    weather_data = scrape_weather_data(city_data.get("latitude"), city_data.get("longitude"))
    await update.message.reply_text(weather_data)


def main() -> None:
    """Main loop and some settings"""
    # Load .env content as Env vars
    load_dotenv()
    application = Application.builder().token(os.environ.get("TG_API_TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, weather_handler))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
