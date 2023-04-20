import json
import pytz
import spacy
import logging
import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# import the required Telegram modules
from telegram import Update
from telegram.ext import (
    CommandHandler,
    ApplicationBuilder,
    ContextTypes,
    filters,
    MessageHandler,
    ConversationHandler,
)

# import the Telegram API token from config.py
from config import TELEGRAM_API_TOKEN

TELEGRAM_API_TOKEN = TELEGRAM_API_TOKEN

# enable logging
logging.basicConfig(level=logging.INFO)

# load pre-trained spacy model
nlp = spacy.load("en_core_web_sm")

# declare constants for ConversationHandler
CITY, NEW_CITY = range(2)


# define function to start the conversation
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("en_strings.json", "r") as f:
        strings = json.load(f)
    welcome_message = strings["welcome_message"]
    await update.message.reply_text(welcome_message)
    # ask the user for a city name
    await update.message.reply_text("Please enter a city name:")
    # return CITY state to indicate that the next message should be a city name
    return CITY


# define function to handle the city message
async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    timezone = get_timezone_from_location(user_text)
    if timezone is None:
        await update.message.reply_text(
            "Sorry, I couldn't recognize that city. Please enter another city name."
        )
        return CITY
    else:
        city_time = get_current_time_in_timezone(timezone)
        await update.message.reply_text(
            f"The time in {user_text} is {city_time}.\n\nIf you want to check another city, "
            f"please enter its name."
        )
        # change the current state to NEW_CITY to indicate that we're waiting for a new city name
        return NEW_CITY


# define function to handle new city messages
async def handle_new_city(update, context):
    user_text = update.message.text
    timezone = get_timezone_from_location(user_text)
    if timezone is None:
        await update.message.reply_text(
            f"Sorry, I couldn't recognize {user_text} as a city. Please enter another "
            f"city name."
        )
    else:
        city_time = get_current_time_in_timezone(timezone)
        await update.message.reply_text(f"The time in {user_text} is {city_time}.")
    # stay in the NEW_CITY state
    return NEW_CITY


# define function to retrieve the time zone from location data
def get_timezone_from_location(city_name):
    geolocator = Nominatim(user_agent="timezone_bot")
    location = geolocator.geocode(city_name, timeout=10)
    if location is None:
        return None
    tf = TimezoneFinder()
    timezone_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
    return timezone_name


# define function to get the current time in a time zone
def get_current_time_in_timezone(timezone_name):
    timezone = pytz.timezone(timezone_name)
    city_time = datetime.datetime.now(timezone)
    return city_time.strftime("%Y-%m-%d %H:%M:%S")


def main():
    # set Telegram bot
    application = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

    # create a conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CITY: [MessageHandler(filters.TEXT, handle_city)],
            NEW_CITY: [MessageHandler(filters.TEXT, handle_new_city)],
        },
        fallbacks=[],
    )
    application.add_handler(conv_handler)

    # start the Telegram bot
    application.run_polling()


if __name__ == "__main__":
    main()
