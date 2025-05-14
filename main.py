import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

API_TOKEN = "7782454356:AAHErZCbWW7FaOHpuFXe1KG4s8xO_AWTITo"  # ← Bot tokeningizni yozing

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

ADMINS = [6655165931, 151222479, 555666777]
user_data = {}
GROUPS = set()  # Guruhlar ro'yxati

# Fayldan guruhlarni yuklash
def load_groups():
    global GROUPS
    try:
        with open("groups.json", "r") as f:
            GROUPS = set(json.load(f))
    except FileNotFoundError:
        GROUPS = set()

# Guruhlarni faylga saqlash
def save_groups():
    with open("groups.json", "w") as f:
        json.dump(list(GROUPS), f)


menu_uz = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📢 Avtorassilka"), KeyboardButton(text="🚛 Yuk qidirish")]],
    resize_keyboard=True
)

menu_ru = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📢 Рассылка"), KeyboardButton(text="🚛 Поиск груза")]],
    resize_keyboard=True
)


class CargoSearch(StatesGroup):
    from_location = State()
    to_location = State()
    cargo_type = State()


cargo_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="cargo_approve"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data="cargo_reject")
    ]
])


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
        msg = "Matnni yuboring (hammaga va guruhlarga yuboriladi):" if lang == "uz" else "Отправьте текст для рассылки:"
        await message.answer(msg)
    else:
        await message.answer("Faqat adminlar uchun." if lang == "uz" else "Только для админа.")


@dp.message(F.text.in_(["🚛 Yuk qidirish", "🚛 Поиск груза"]))
async def gruz_start(message: Message, state: FSMContext):
    await state.set_state(CargoSearch.from_location)
    lang = user_data.get(message.from_user.id, {}).get("lang", "uz")
    msg = "Yuk qayerdan jo'natiladi?" if lang == "uz" else "Откуда груз?"
    await message.answer(msg)


@dp.message(CargoSearch.from_location)
async def get_from(message: Message, state: FSMContext):
    await state.update_data(from_location=message.text)
    await state.set_state(CargoSearch.to_location)
    lang = user_data.get(message.from_user.id, {}).get("lang", "uz")
    await message.answer("Yuk qayerga yetkaziladi?" if lang == "uz" else "Куда доставить груз?")


@dp.message(CargoSearch.to_location)
async def get_to(message: Message, state: FSMContext):
    await state.update_data(to_location=message.text)
    await state.set_state(CargoSearch.cargo_type)
    lang = user_data.get(message.from_user.id, {}).get("lang", "uz")
    await message.answer("Yuk turi qanday?" if lang == "uz" else "Какой тип груза?")


@dp.message(CargoSearch.cargo_type)
async def get_type(message: Message, state: FSMContext):
    await state.update_data(cargo_type=message.text)
    data = await state.get_data()
    lang = user_data.get(message.from_user.id, {}).get("lang", "uz")

    msg = (
        f"📦 <b>Yuk qidiruv:</b>\n"
        f"📍 Qayerdan: {data['from_location']}\n"
        f"📍 Qayerga: {data['to_location']}\n"
        f"🚛 Yuk turi: {data['cargo_type']}\n"
        f"👤 @{message.from_user.username or message.from_user.full_name}"
    ) if lang == "uz" else (
        f"📦 <b>Поиск груза:</b>\n"
        f"📍 Откуда: {data['from_location']}\n"
        f"📍 Куда: {data['to_location']}\n"
        f"🚛 Тип груза: {data['cargo_type']}\n"
        f"👤 @{message.from_user.username or message.from_user.full_name}"
    )

    for admin in ADMINS:
        try:
            await bot.send_message(admin, msg, parse_mode=ParseMode.HTML, reply_markup=cargo_keyboard)
        except:
            continue

    await message.answer("So‘rovingiz yuborildi." if lang == "uz" else "Ваш запрос отправлен.")
    await state.clear()


@dp.callback_query(F.data.in_(["cargo_approve", "cargo_reject"]))
async def handle_cargo_action(call: CallbackQuery):
    action = "✅ Tasdiqlandi" if call.data == "cargo_approve" else "❌ Rad etildi"
    new_text = f"{call.message.text}\n\n<b>{action}</b>"
    await call.message.edit_text(new_text, parse_mode=ParseMode.HTML)
    await call.answer("Holat belgilandi")


@dp.message()
async def handle_all_messages(message: Message):
    # Guruhdan xabar kelsa — ro‘yxatga qo‘shamiz
    if message.chat.type in ("group", "supergroup"):
        if message.chat.id not in GROUPS:
            GROUPS.add(message.chat.id)
            save_groups()
            print(f"[INFO] Guruh qo‘shildi: {message.chat.title} ({message.chat.id})")

    # Admin avtorassilka yuborgan bo‘lsa — barcha userlarga va guruhlarga yuboriladi
    if message.from_user.id in ADMINS:
        for user_id in user_data:
            try:
                await bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
            except:
                continue

        for group_id in GROUPS:
            try:
                await bot.copy_message(chat_id=group_id, from_chat_id=message.chat.id, message_id=message.message_id)
            except Exception as e:
                print(f"Guruhga yuborilmadi: {e}")


async def main():
    logging.basicConfig(level=logging.INFO)
    load_groups()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
