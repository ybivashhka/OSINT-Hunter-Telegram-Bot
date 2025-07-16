import aiohttp
from aiohttp import ClientSession
from osint_hunter.config import HAVEIBEENPWNED_API_KEY

async def search_by_email(email: str) -> dict:
    try:
        async with ClientSession() as session:
            headers = {"hibp-api-key": HAVEIBEENPWNED_API_KEY}
            url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
            async with session.get(url, headers=headers) as response:
                if response.status == 404:
                    return {"result": f"Email {email} не найден в утечках."}
                elif response.status != 200:
                    return {"result": f"Ошибка API: статус {response.status}"}
                data = await response.json()
                return {"result": f"Утечки для {email}: {data}"}
    except Exception as e:
        return {"result": f"Ошибка при поиске по email: {str(e)}"}