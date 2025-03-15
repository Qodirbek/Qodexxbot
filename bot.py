import asyncio
import json
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = "8064942614:AAGT-8nE_MmK45WAdv7VCChaK8jo8O1lNzU"
ADMIN_ID = 6494723214  # O'z Telegram ID'ingizni shu yerga yozing

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

USERS_FILE = "users.json"

# Foydalanuvchilar ro‘yxatini saqlash
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# Botga yangi foydalanuvchi qo‘shish
def add_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)

# Admin paneli uchun holatlar
class BroadcastState(StatesGroup):
    waiting_for_message = State()
    waiting_for_button_text = State()
    waiting_for_button_url = State()

# Boshlang‘ich /start komandasi
@router.message(Command("start"))
async def start_command(message: types.Message):
    add_user(message.from_user.id)
    
    text = "👋 Salom!\nBu QODEX o'yinining rasmiy Telegram boti. Quyidagi tugmalardan birini tanlang:"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Play Game", web_app=WebAppInfo(url="https://qodex-game.onrender.com/"))],
        [InlineKeyboardButton(text="💋💪 Join Community", url="https://t.me/QODEX_COIN")],
        [InlineKeyboardButton(text="SUPPORT", url="https://t.me/QODEX_Support_Admin_bot")]
    ])

    await message.answer(text, reply_markup=keyboard)

# **ADMIN PANELI**
@router.message(Command("Qodirbek_2007_Admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="show_stats")],
        [InlineKeyboardButton(text="📢 Send Message", callback_data="send_broadcast")],
        [InlineKeyboardButton(text="🚪 Chiqish", callback_data="exit_admin")]
    ])
    
    await message.answer("👑 Admin paneliga xush kelibsiz!", reply_markup=keyboard)

# **STATISTIKA (foydalanuvchilar sonini ko‘rsatish)**
@router.callback_query(lambda c: c.data == "show_stats")
async def show_stats(callback: types.CallbackQuery):
    users = load_users()
    await callback.message.answer(f"📊 Botdan foydalanuvchilar soni: {len(users)}")
    await callback.answer()

# **ADMIN PANELIDAN CHIQISH**
@router.callback_query(lambda c: c.data == "exit_admin")
async def exit_admin(callback: types.CallbackQuery):
    await callback.message.answer("✅ Admin panelidan chiqdingiz.")
    await callback.answer()

# **BARCHA FOYDALANUVCHILARGA XABAR YUBORISH BOSQICHI**
@router.callback_query(lambda c: c.data == "send_broadcast")
async def start_broadcast(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📢 Yuboriladigan xabarni kiriting:")
    await state.set_state(BroadcastState.waiting_for_message)
    await callback.answer()

# **Xabar qabul qilish va tugma qo‘shish taklifi**
@router.message(BroadcastState.waiting_for_message)
async def receive_message(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Tugma qo‘shish", callback_data="add_button")],
        [InlineKeyboardButton(text="✅ Tugmasiz yuborish", callback_data="send_without_button")]
    ])
    await message.answer("📌 Tugma qo‘shishni xohlaysizmi?", reply_markup=keyboard)

# **Tugma qo‘shish bosqichi**
@router.callback_query(lambda c: c.data == "add_button")
async def ask_button_text(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("🔘 Tugma matnini kiriting:")
    await state.set_state(BroadcastState.waiting_for_button_text)
    await callback.answer()

@router.message(BroadcastState.waiting_for_button_text)
async def receive_button_text(message: types.Message, state: FSMContext):
    await state.update_data(button_text=message.text)
    await message.answer("🔗 Tugma URL manzilini kiriting:")
    await state.set_state(BroadcastState.waiting_for_button_url)

@router.message(BroadcastState.waiting_for_button_url)
async def receive_button_url(message: types.Message, state: FSMContext):
    await state.update_data(button_url=message.text)
    await send_broadcast(state, message)

# **Tugmasiz xabar yuborish**
@router.callback_query(lambda c: c.data == "send_without_button")
async def send_without_button(callback: types.CallbackQuery, state: FSMContext):
    await send_broadcast(state, callback.message)

# **Barcha foydalanuvchilarga xabar yuborish**
async def send_broadcast(state: FSMContext, message: types.Message):
    data = await state.get_data()
    text = data.get("text")
    button_text = data.get("button_text")
    button_url = data.get("button_url")

    users = load_users()
    sent_count = 0

    keyboard = None
    if button_text and button_url:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_text, url=button_url)]
        ])

    for user_id in users:
        try:
            await bot.send_message(user_id, text, reply_markup=keyboard)
            sent_count += 1
        except:
            pass

    await message.answer(f"✅ Xabar {sent_count} ta foydalanuvchiga yuborildi!")
    await state.clear()

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())