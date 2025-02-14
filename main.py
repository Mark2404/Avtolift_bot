from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
import logging
import asyncio

# # Токен бота
# TOKEN = "7568958401:AAH0GfSvDG7Rcja5lEHj0yK38eOqTX0SI64"
# OWNER_ID = 6850746500  # Замени на свой Telegram ID
import os
TOKEN = os.getenv("TOKEN")
OWNER_ID = os.getenv("OWNER_ID")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Логирование
logging.basicConfig(level=logging.INFO)

user_data = {}

contact_numbers = "📞 Контактные номера: +998936825005, +998336071000"

lang_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"), InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")]
])

categories_keyboard = {
    "ru": InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 с 2 до 8 этажа", callback_data="cat_2_8")],
        [InlineKeyboardButton(text="🚌 с 8 до 16 этажа", callback_data="cat_8_16")]
    ]),
    "uz": InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 2 qavatdan 8 qavatgacha", callback_data="cat_2_8")],
        [InlineKeyboardButton(text="🚌 8 qavatdan 16 qavatgacha", callback_data="cat_8_16")]
    ])
}

order_keyboard = {
    "ru": InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back"), InlineKeyboardButton(text="✅ Заказать", callback_data="order")]
    ]),
    "uz": InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back"), InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="order")]
    ])
}

repeat_order_keyboard = {
    "ru": ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔄 Повторить заказ")]], resize_keyboard=True
    ),
    "uz": ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔄 Buyurtmani qayta boshlash")]], resize_keyboard=True
    )
}

async def start_command(message: types.Message):
    await message.answer("Привет! Xush kelibsiz!\nВыберите язык / Tilni tanlang:", reply_markup=lang_keyboard)
dp.message.register(start_command, Command("start"))

async def set_language(callback_query: types.CallbackQuery):
    lang = callback_query.data.split("_")[1]
    user_data[callback_query.from_user.id] = {"lang": lang}
    text = "Выберите на какой этаж вам надо поднять" if lang == "ru" else "Nechanchi qavatga opchiqishni tanlang:"
    await callback_query.message.edit_text(text, reply_markup=categories_keyboard[lang])
    await callback_query.message.answer(contact_numbers)
dp.callback_query.register(set_language, lambda c: c.data.startswith("lang_"))

async def select_category(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "ru")
    category = "с 2 до 8 этажа" if callback_query.data == "cat_2_8" else "с 8 до 16 этажа"
    category_uz = "2 qavatdan 8 gacha" if callback_query.data == "cat_2_8" else "8 qavatdan 16 gacha"
    user_data[user_id]["category"] = category if lang == "ru" else category_uz
    text = "Вы выбрали: " + (category if lang == "ru" else category_uz)
    await callback_query.message.edit_text(text, reply_markup=order_keyboard[lang])
dp.callback_query.register(select_category, lambda c: c.data.startswith("cat_"))

async def order_service(callback_query: types.CallbackQuery):
    lang = user_data.get(callback_query.from_user.id, {}).get("lang", "ru")
    text = "Отправьте вашу локацию" if lang == "ru" else "Lokatsiyangizni yuboring"
    await callback_query.message.answer(text, reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Отправить локацию" if lang == "ru" else "📍 Lokatsiyani yuborish", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    ))
dp.callback_query.register(order_service, lambda c: c.data == "order")

async def handle_location(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["location"] = message.location
    lang = user_data[user_id].get("lang", "ru")
    text = "📞 Отправьте ваш номер телефона" if lang == "ru" else "📞 Telefon raqamingizni yuboring"
    await message.answer(text, reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Отправить номер" if lang == "ru" else "📞 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    ))
dp.message.register(handle_location, lambda m: m.content_type == types.ContentType.LOCATION)

async def handle_contact(message: types.Message):
  import logging

async def handle_contact(message: types.Message):
    user_id = message.from_user.id
    logging.info(f"Получен контакт от {user_id}: {message.contact}")

    if user_id not in user_data:
        user_data[user_id] = {}

    phone_number = message.contact.phone_number if message.contact else message.text
    user_data[user_id]["phone"] = phone_number
    
    location = user_data[user_id].get("location", None)
    category = user_data[user_id].get("category", "Не указано")

    location_link = f"https://maps.google.com/?q={location.latitude},{location.longitude}" if location else "Локация не найдена"
    
    text = f"📌 Новый заказ!\n👤 Имя: {message.from_user.full_name}\n📞 Телефон: {phone_number}\n🏢 Этаж: {category}\n🌍 Локация: {location_link}"
    
    logging.info(f"Отправка заказа владельцу: {text}")

    await bot.send_message(OWNER_ID, text)
    await message.answer("✅ Ваш заказ отправлен! Мы скоро с вами свяжемся!", reply_markup=repeat_order_keyboard[user_data[user_id]["lang"]])


async def repeat_order(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {}
    await start_command(message)
dp.message.register(repeat_order, lambda m: m.text in ["🔄 Повторить заказ", "🔄 Buyurtmani qayta boshlash"])

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
