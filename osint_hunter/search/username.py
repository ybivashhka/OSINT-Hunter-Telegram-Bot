import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from osint_hunter.config import LEAKCHECK_API_KEY

async def search_by_username(username: str) -> dict:
    try:
        async with ClientSession() as session:
            # Пример запроса к LeakCheck
            url = f"https://leakcheck.io/api?key={LEAKCHECK_API_KEY}&check={username}&type=username"
            async with session.get(url) as response:
                if response.status != 200:
                    return {"result": f"Ошибка API: статус {response.status}"}
                data = await response.json()
                return {"result": f"Результат поиска по имени пользователя {username}: {data}"}
    except Exception as e:
        return {"result": f"Ошибка при поиске по имени пользователя: {str(e)}"}