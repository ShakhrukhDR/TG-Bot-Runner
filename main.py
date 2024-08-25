import logging
import asyncio
import random
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, BotCommand, ReplyKeyboardMarkup, KeyboardButton
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import config

# Настройка логирования
logging.basicConfig(level=logging.INFO)

API_TOKEN = config.token
WEATHER_API_KEY = config.weather_api_key

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

geolocator = Nominatim(user_agent="ai_sp_test_bot")
tf = TimezoneFinder()

user_data = {}

# Создание клавиатуры с кнопками
def get_main_keyboard():
    buttons = [
        [KeyboardButton(text="/time"), KeyboardButton(text="/weather")],
        [KeyboardButton(text="/random")],
        [KeyboardButton(text="/info"), KeyboardButton(text="/about")],
        [KeyboardButton(text="Сменить город")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Установка команд для меню бота
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/help", description="Список доступных команд"),
        BotCommand(command="/info", description="Информация о боте"),
        BotCommand(command="/about", description="О боте"),
        BotCommand(command="/time", description="Узнать текущее время"),
        BotCommand(command="/weather", description="Узнать погоду"),
        BotCommand(command="/random", description="Получить случайное число")
    ]
    await bot.set_my_commands(commands)

# Обработчик команды /start
@dp.message(Command(commands=["start"]))
async def start_command(message: Message):
    await message.answer(
        "Привет! Я бот с простыми функциями. В каком городе ты находишься? Пожалуйста, введи название города.",
        reply_markup=get_main_keyboard()
    )

# Обработчик команды /help
@dp.message(Command(commands=["help"]))
async def help_command(message: Message):
    help_text = (
        "/start - Запустить бота\n"
        "/help - Список доступных команд\n"
        "/info - Информация о боте\n"
        "/about - О боте\n"
        "/time - Узнать текущее время\n"
        "/weather - Узнать погоду\n"
        "/random - Получить случайное число"
    )
    await message.answer(help_text, reply_markup=get_main_keyboard())

# Обработчик команды /info
@dp.message(Command(commands=["info"]))
async def info_command(message: Message):
    await message.answer(
        "Это информация о боте. Он предназначен для демонстрации простейших функций.",
        reply_markup=get_main_keyboard()
    )

# Обработчик команды /about
@dp.message(Command(commands=["about"]))
async def about_command(message: Message):
    await message.answer(
        "Этот бот написан на Python с использованием библиотеки Aiogram.",
        reply_markup=get_main_keyboard()
    )

# Обработчик команды /time
@dp.message(Command(commands=["time"]))
async def time_command(message: Message):
    user_info = user_data.get(message.from_user.id)
    if user_info:
        timezone_name = user_info["timezone_name"]
        current_time = datetime.now(ZoneInfo(timezone_name))
        formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        await message.answer(
            f"Текущее время в твоем городе ({user_info['city']}): {formatted_time}",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "Пожалуйста, сначала укажи свой город, чтобы я мог показать правильное время. Введи свой город:",
            reply_markup=get_main_keyboard()
        )

# Обработчик команды /weather
@dp.message(Command(commands=["weather"]))
async def weather_command(message: Message):
    user_info = user_data.get(message.from_user.id)
    if user_info:
        city = user_info["city"]
        weather = get_weather(city)
        if weather:
            await message.answer(
                f"Погода в городе {city}:\n{weather}",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                f"Не удалось получить информацию о погоде для города {city}.",
                reply_markup=get_main_keyboard()
            )
    else:
        await message.answer(
            "Пожалуйста, сначала укажи свой город, чтобы я мог показать правильную погоду. Введи свой город:",
            reply_markup=get_main_keyboard()
        )

# Обработчик команды /random
@dp.message(Command(commands=["random"]))
async def random_command(message: Message):
    random_number = random.randint(1, 100)
    await message.answer(
        f"Ваше случайное число: {random_number}",
        reply_markup=get_main_keyboard()
    )

# Обработка смены города
@dp.message(lambda message: message.text == "Сменить город")
async def change_city(message: Message):
    await message.answer(
        "Пожалуйста, введи название нового города.",
        reply_markup=get_main_keyboard()
    )

# Обработка ввода города
@dp.message()
async def set_city(message: Message):
    city = message.text.strip()
    if city.startswith("/"):  # Игнорируем команды
        return
    try:
        location = geolocator.geocode(city)
        if location:
            timezone_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            user_data[message.from_user.id] = {
                "timezone_name": timezone_name,
                "city": city
            }
            await message.answer(
                f"Город установлен на {city}. Введи /time или /weather, чтобы узнать текущее время или погоду.",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                "Не удалось найти этот город. Пожалуйста, попробуй еще раз.",
                reply_markup=get_main_keyboard()
            )
    except Exception as e:
        await message.answer(
            f"Произошла ошибка: {str(e)}",
            reply_markup=get_main_keyboard()
        )

def get_weather(city: str) -> str:
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={WEATHER_API_KEY}&lang=ru"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        weather_desc = data['weather'][0]['description']
        temp = data['main']['temp']
        return f"{weather_desc.capitalize()}, температура: {temp}°C"
    return None

# Запуск бота
async def main():
    await set_commands(bot)  # Установка команд для меню
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
