import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

API_TOKEN = "7782454356:AAHErZCbWW7FaOHpuFXe1KG4s8xO_AWTITo"  # ← Bu yerga bot tokeningizni yozing

# Bot va dispatcher
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# ✅ 3 ta admin ID
ADMINS = [6655165931, 151222479,]
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


# ✅ Yuk qidirish FSM
class CargoSearch(StatesGroup):
    from_location = State()
    to_location = State()
    cargo_type = State()


@dp.message(F.text.in_(["🚛 Yuk qidirish", "🚛 Поиск груза"]))
async def gruz_poisk(message: Message, state: FSMContext):
    lang = user_data.get(message.from_user.id, {}).get("lang", "uz")
    msg = "Yuk qayerdan jo'natiladi?" if lang == "uz" else "Откуда груз?"
    await state.set_state(CargoSearch.from_location)
    await message.answer(msg)


@dp.message(CargoSearch.from_location)
async def get_from_location(message: Message, state: FSMContext):
    await state.update_data(from_location=message.text)
    await state.set_state(CargoSearch.to_location)
    await message.answer("Yuk qayerga yetkaziladi?" if user_data.get(message.from_user.id, {}).get("lang", "uz") == "uz"
                         else "Куда доставить груз?")


@dp.message(CargoSearch.to_location)
async def get_to_location(message: Message, state: FSMContext):
    await state.update_data(to_location=message.text)
    await state.set_state(CargoSearch.cargo_type)
    await message.answer("Yuk turi qanday?" if user_data.get(message.from_user.id, {}).get("lang", "uz") == "uz"
                         else "Какой тип груза?")


@dp.message(CargoSearch.cargo_type)
async def get_cargo_type(message: Message, state: FSMContext):
    await state.update_data(cargo_type=message.text)
    data = await state.get_data()
    lang = user_data.get(message.from_user.id, {}).get("lang", "uz")

    msg = (
        f"📦 <b>Yuk qidiruv:</b>\n"
        f"📍 Qayerdan: {data['from_location']}\n"
        f"📍 Qayerga: {data['to_location']}\n"
        f"🚛 Yuk turi: {data['cargo_type']}\n"
        f"👤 Foydalanuvchi: @{message.from_user.username or message.from_user.full_name}"
    ) if lang == "uz" else (
        f"📦 <b>Поиск груза:</b>\n"
        f"📍 Откуда: {data['from_location']}\n"
        f"📍 Куда: {data['to_location']}\n"
        f"🚛 Тип груза: {data['cargo_type']}\n"
        f"👤 Пользователь: @{message.from_user.username or message.from_user.full_name}"
    )

    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, msg, parse_mode=ParseMode.HTML)
        except:
            continue

    await message.answer("So‘rovingiz yuborildi. Tez orada siz bilan bog‘lanishadi." if lang == "uz"
                         else "Ваш запрос отправлен. Скоро с вами свяжутся.")
    await state.clear()


# ✅ Admin yuborgan xabar (matn, media, link...) — barcha foydalanuvchilarga yuboriladi
@dp.message()
async def send_to_all(message: Message):
    if message.from_user.id in ADMINS:
        for user_id in user_data:
            try:
                await bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
            except Exception as e:
                print(f"Xatolik: {e}")
                continue
        lang = user_data.get(message.from_user.id, {}).get("lang", "uz")
        await message.reply("Xabar yuborildi." if lang == "uz" else "Сообщение отправлено.")


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
