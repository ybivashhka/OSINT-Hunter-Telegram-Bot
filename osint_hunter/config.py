import os
from dotenv import load_dotenv

load_dotenv()

# Токен Telegram-бота, полученный от @BotFather
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
# Ключ API для HaveIBeenPwned (https://haveibeenpwned.com/API/Key)
HAVEIBEENPWNED_API_KEY = os.getenv('HAVEIBEENPWNED_API_KEY')
# Ключ API для LeakCheck (https://leakcheck.io/api)
LEAKCHECK_API_KEY = os.getenv('LEAKCHECK_API_KEY')

if not all([TELEGRAM_TOKEN, HAVEIBEENPWNED_API_KEY, LEAKCHECK_API_KEY]):
    raise RuntimeError("Один или несколько API-ключей не найдены в переменных окружения!")