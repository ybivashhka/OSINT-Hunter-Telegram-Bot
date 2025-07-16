from aiologger import Logger
from aiologger.handlers.files import AsyncFileHandler
from typing import Optional

logger = Logger()
handler = AsyncFileHandler('osint_audit.log')
formatter = '%(asctime)s - %(user_id)s - %(action)s - %(message)s'
handler.formatter = formatter
logger.add_handler(handler)

async def log_action(user_id: str, action: str, message: str = ""):
    try:
        await logger.info(message, extra={'user_id': user_id, 'action': action})
    except IOError as e:
        print(f"Ошибка записи в лог: {e}")