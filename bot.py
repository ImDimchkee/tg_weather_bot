import os
import logging

from dotenv import load_dotenv

# Telegram api imports
# ref: https://docs.python-telegram-bot.org/
from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# Cat images api import
import cat

# Open-meteo module import
from open_meteo import geocoding_search_city, scrape_weather_data


# logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Disables log clutter due to lots of httpx calls
logging.getLogger("httpx").disabled = True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Bot entry point

    Args:
        update (Update): Incoming update containing a user message.
        context (ContextTypes.DEFAULT_TYPE): Contextual information about the update.
    """
    logger.info(f"%s User issues a /start command", update.effective_user.id)

    await update.message.reply_text(
        "Welcome, Flipper! 🐬\n\n"
        "This bot can check air quality and weather for any city you send me (in English).\n\n"
        "Just type the city name, and I’ll fetch the latest data for you.\n\n"
        "Use the /help command to see full usage instructions. 😉"
    )


async def weather_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Scrape weather conditions data based on provided input location

    Args:
        update (Update): Incoming update containing a user message.
        context (ContextTypes.DEFAULT_TYPE): Contextual information about the update.
    """
    city_name = update.message.text.strip()
    logger.info(f"Received city query for %s", city_name)

    try:
        city_data = geocoding_search_city(city_name)
        weather_data = scrape_weather_data(
            city_data.get("latitude"), city_data.get("longitude")
        )

        logger.info(f"Successfully pulled weather data from API: %s", weather_data)

        await update.message.reply_text(
            f"*📍 Location found: {city_name}*\n"
            f"Latitude: {city_data.get('latitude')}\n"
            f"Longitude: {city_data.get('longitude')}\n\n"
            "*🌤 Current Air Quality Conditions:*\n"
            f"- PM10: {weather_data.get('current_pm10')}\n"
            f"- PM2.5: {weather_data.get('current_pm2_5')}\n"
            f"- CO (Carbon Monoxide): {weather_data.get('current_carbon_monoxide')}",
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Error fetching weather data for %s: %s", city_name, e)
        await update.message.reply_text(
            "An error occurred while retrieving weather data."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Sends the user help manual on bot's functionality

    Args:
        update (Update): Incoming update containing a user message.
        context (ContextTypes.DEFAULT_TYPE): Contextual information about the update.
    """
    logger.info(f"%s User issues a /help command", update.effective_user.id)

    await update.message.reply_text(
        "*What this bot can do?*❔\n\
    - If you send actual city name in English to this bot,\n\
      it will lookup its coordinates using public API\n\
      Then it queries various metrics from the same API.\n\
\n\
    - Implemented metrics are:\n\
      pm10 - particles smaller than 10µm\n\
      pm2.5 - particles smaller than 2.5µm\n\
      Carbon monoxide (CO) level - Poisonous gas\n\
\n\
    - Commands list:\n\
      /start to display welcoming message\n\
      /help to display this menu again\n\
      /cat to get a random cat image",
        parse_mode="Markdown",
    )


async def cat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for cat command, downloads and sends random cat pic to the user

    Args:
        update (Update): Incoming update containing a user message.
        context (ContextTypes.DEFAULT_TYPE): Contextual information about the update.
    """
    logger.info(
        f"%s User issued /cat command, downloading...", update.effective_user.id
    )
    try:
        cat_image_path = cat.getCat(format="png")
        await update.message.reply_photo(
            cat_image_path, caption="Here's a random cat pic 🐈"
        )
    except Exception as e:
        logger.error(f"Got an exception during image download:\n%s", e)
        await update.message.reply_text(
            "Sorry, I can't get you a pic of a cat this time 😿"
        )
    finally:
        if os.path.exists(cat_image_path):
            os.remove(cat_image_path)
            logger.info("Successfully removed leftover files")


def main() -> None:
    """
    Loads environment variables, configures the bot, and starts polling for updates.
    """
    load_dotenv()
    application = (
        Application.builder()
        .token(os.environ.get("TG_API_TOKEN"))
        .read_timeout(10)
        .connect_timeout(10)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cat", cat_command))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, weather_handler)
    )

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
