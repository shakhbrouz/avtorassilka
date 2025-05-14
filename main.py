import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

API_TOKEN = "7782454356:AAHErZCbWW7FaOHpuFXe1KG4s8xO_AWTITo"  # ← Bu yerga bot tokeningizni yozing

# Bot va dispatcher
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

ADMINS = [6655165931]  # ← O'zingizning Telegram ID'ingizni yozing
user_data = {}

# Menular
menu_uz = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📢 Avtorassilka"), KeyboardButton(text="🚛 Yuk qidirish")]
    ],
    resize_keyboard=True
)

menu_ru = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📢 Рассылка"), KeyboardButton(text="🚛 Поиск груза")]
    ],
    resize_keyboard=True
)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_data[message.from_user.id] = {'lang': 'uz'}
    await message.answer(
        "Tilni tanlang / Выберите язык",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="O‘zbekcha"), KeyboardButton(text="Русский")]],
            resize_keyboard=True
        )
    )


@dp.message(F.text.in_(["O‘zbekcha", "Русский"]))
async def set_language(message: Message):
    lang = "uz" if message.text == "O‘zbekcha" else "ru"
    user_data[message.from_user.id] = {'lang': lang}
    markup = menu_uz if lang == "uz" else menu_ru
    welcome = "Xush kelibsiz! Kerakli bo‘limni tanlang 👇" if lang == "uz" else "Добро пожаловать! Выберите раздел 👇"
    await message.answer(welcome, reply_markup=markup)


@dp.message(F.text.in_(["📢 Avtorassilka", "📢 Рассылка"]))
async def avtorassilka(message: Message):
    lang = user_data.get(message.from_user.id, {}).get("lang", "uz")
    if message.from_user.id in ADMINS:
        msg = "Matnni yuboring (hammaga yuboriladi):" if lang == "uz" else "Отправьте текст для рассылки:"
        await message.answer(msg)
    else:
        await message.answer("Faqat adminlar uchun." if lang == "uz" else "Только для админа.")


@dp.message(F.text.in_(["🚛 Yuk qidirish", "🚛 Поиск груза"]))
async def gruz_poisk(message: Message):
    lang = user_data.get(message.from_user.id, {}).get("lang", "uz")
    msg = "Yuk qidirish xizmati tez orada ishga tushadi!" if lang == "uz" else "Сервис поиска груза скоро будет запущен!"
    await message.answer(msg)


@dp.message()
async def send_to_all(message: Message):
    if message.from_user.id in ADMINS:
        for user_id in user_data:
            try:
                await bot.send_message(user_id, message.text)
            except:
                continue
        lang = user_data.get(message.from_user.id, {}).get("lang", "uz")
        await message.answer("Xabar yuborildi." if lang == "uz" else "Сообщение отправлено.")


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
