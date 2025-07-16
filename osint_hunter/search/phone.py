import aiohttp
from aiohttp import ClientSession
from phonenumbers import parse, is_valid_number
from osint_hunter.config import LEAKCHECK_API_KEY

async def search_by_phone(phone: str) -> dict:
    try:
        parsed_phone = parse(phone, None)
        if not is_valid_number(parsed_phone):
            return {"result": "Некорректный номер телефона."}
        async with ClientSession() as session:
            url = f"https://leakcheck.io/api?key={LEAKCHECK_API_KEY}&check={phone}&type=phone"
            async with session.get(url) as response:
                if response.status != 200:
                    return {"result": f"Ошибка API: статус {response.status}"}
                data = await response.json()
                return {"result": f"Результат поиска по телефону {phone}: {data}"}
    except Exception as e:
        return {"result": f"Ошибка при поиске по телефону: {str(e)}"}