import re
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.dispatcher.middlewares import BaseMiddleware
from time import time
from osint_hunter.config import TELEGRAM_TOKEN
from osint_hunter.logger import log_action
from osint_hunter.search.username import search_by_username
from osint_hunter.search.email import search_by_email
from osint_hunter.search.phone import search_by_phone
from osint_hunter.search.ipwhois import search_by_ip
from phonenumbers import is_valid_number, parse as parse_phone

# Inline-клавиатура для выбора типа поиска
search_keyboard = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [types.InlineKeyboardButton(text="Username", callback_data="search_username")],
        [types.InlineKeyboardButton(text="Email", callback_data="search_email")],
        [types.InlineKeyboardButton(text="Телефон", callback_data="search_phone")],
        [types.InlineKeyboardButton(text="IP/WHOIS", callback_data="search_ip")],
    ]
)

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN не найден в переменных окружения!")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
router = Router()

# Состояние поиска для каждого пользователя
user_search_state = {}

# Middleware для ограничения частоты запросов
class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit=10, window=60):
        self.limit = limit
        self.window = window
        self.user_requests = {}

    async def on_process_message(self, message: types.Message, data: dict):
        user_id = message.from_user.id
        current_time = time()
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        self.user_requests[user_id] = [t for t in self.user_requests[user_id] if current_time - t < self.window]
        if len(self.user_requests[user_id]) >= self.limit:
            await message.reply("Слишком много запросов. Попробуйте позже.")
            return
        self.user_requests[user_id].append(current_time)

# Валидация ввода
def validate_email(email: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def validate_ip(ip: str) -> bool:
    return bool(re.match(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', ip))

# Маскировка чувствительных данных для логов
def mask_sensitive_data(query: str, search_type: str) -> str:
    if search_type == "email":
        parts = query.split("@")
        return f"{parts[0][:2]}***@{parts[1]}" if len(parts) == 2 else query
    elif search_type == "phone":
        return f"{query[:4]}***{query[-2:]}" if len(query) > 6 else query
    return query

@router.message(commands=["start", "help"])
async def send_welcome(message: types.Message):
    user_id = str(message.from_user.id) if message.from_user else 'unknown'
    await message.answer(
        "Привет! Я OSINT Hunter. Выберите тип поиска:",
        reply_markup=search_keyboard
    )
    await log_action(user_id, "start", "Пользователь начал работу с ботом.")

@router.callback_query(F.data.startswith("search_"))
async def process_search_type(callback: types.CallbackQuery):
    if not callback.data or "_" not in callback.data:
        await callback.answer("Некорректный тип поиска.")
        return
    if not callback.message:
        await callback.answer("Ошибка: не найдено сообщение. Попробуйте /start.")
        return
    search_type = callback.data.split("_", 1)[1]
    await callback.answer()
    await callback.message.answer(f"Введите {search_type} для поиска:")
    user_id = callback.from_user.id if callback.from_user else None
    await log_action(str(user_id) if user_id else 'unknown', "choose_search_type", f"Выбран тип поиска: {search_type}")
    if user_id:
        user_search_state[user_id] = search_type

@router.message()
async def handle_search(message: types.Message):
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        await message.reply("Ошибка: не удалось определить пользователя.")
        return
    search_type = user_search_state.get(user_id)
    if not search_type:
        await message.reply("Сначала выберите тип поиска через /start.")
        return
    if not message.text:
        await message.reply("Пожалуйста, отправьте текстовое сообщение для поиска.")
        return
    query = message.text.strip()
    masked_query = mask_sensitive_data(query, search_type)
    await log_action(str(user_id), "search_request", f"Тип: {search_type}, Запрос: {masked_query}")

    # Валидация ввода
    if search_type == "email" and not validate_email(query):
        await message.reply("Некорректный email.")
        return
    if search_type == "phone":
        try:
            if not is_valid_number(parse_phone(query, None)):
                await message.reply("Некорректный номер телефона.")
                return
        except Exception:
            await message.reply("Некорректный номер телефона.")
            return
    if search_type == "ip" and not validate_ip(query):
        await message.reply("Некорректный IP-адрес.")
        return

    try:
        if search_type == "username":
            result = await search_by_username(query)
        elif search_type == "email":
            result = await search_by_email(query)
        elif search_type == "phone":
            result = await search_by_phone(query)
        elif search_type == "ip":
            result = await search_by_ip(query)
        else:
            await message.reply("Неизвестный тип поиска.")
            return

        # Разбиение длинных сообщений
        result_text = str(result["result"])
        for i in range(0, len(result_text), 4096):
            await message.reply(result_text[i:i+4096])
        await log_action(str(user_id), "search_success", f"Тип: {search_type}, Запрос: {masked_query}")
        user_search_state.pop(user_id, None)  # Очистка состояния
    except Exception as e:
        await message.reply(f"Ошибка при поиске: {str(e)}")
        await log_action(str(user_id), "search_error", f"Тип: {search_type}, Ошибка: {str(e)}")

dp.include_router(router)
dp.middleware.setup(RateLimitMiddleware())

async def main():
    try:
        await dp.start_polling(bot)
    except Exception as e:
        await log_action("system", "bot_error", f"Ошибка при запуске бота: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())