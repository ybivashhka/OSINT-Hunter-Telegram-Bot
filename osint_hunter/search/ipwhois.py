import aiohttp
from aiohttp import ClientSession
import whois

async def search_by_ip(ip: str) -> dict:
    try:
        w = whois.whois(ip)
        return {"result": f"WHOIS для IP {ip}: {w}"}
    except Exception as e:
        return {"result": f"Ошибка при поиске по IP: {str(e)}"}