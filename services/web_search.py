import asyncio
import logging
from typing import List, Optional

import httpx
import trafilatura
from googleapiclient.discovery import build
from langchain.tools import tool
from schemas import Source
from config import GOOGLE_API_KEY, GOOGLE_CX

log = logging.getLogger(__name__)


def search_google_sync(query: str, num_results: int = 10) -> List[str]:
    """Синхронно выполняет один поисковый запрос в Google и возвращает URL."""
    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
    res = service.cse().list(q=query, cx=GOOGLE_CX, num=num_results).execute()
    items = res.get("items", [])
    return [item.get("formattedUrl", "") for item in items]

async def fetch_and_extract_content(client: httpx.AsyncClient, url: str) -> Optional[Source]:
    """
    Асинхронно скачивает страницу и извлекает основной текст с помощью trafilatura.
    В случае успеха возвращает объект Source, иначе None.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = await client.get(url, headers=headers, timeout=10, follow_redirects=True)
        response.raise_for_status()

        extracted_text = await asyncio.to_thread(trafilatura.extract, response.text)
        
        if extracted_text and len(extracted_text) > 200:
            return Source(url=url, content=extracted_text[:4000])
            
    except Exception as e:
        log.warning(f"Не удалось обработать URL {url}: {e}")
    
    return None

@tool
async def search_and_scrape(query: str) -> List[dict]:
    """
    Ищет информацию в Google, скачивает страницы и извлекает из них
    основной текст с помощью интеллектуального парсера.
    """

    log.info(f"Поиск по запросу: '{query}'")
    urls = await asyncio.to_thread(search_google_sync, query, num_results=10)
    
    log.info(f"Найдено {len(urls)} URL. Извлечение контента")

    async with httpx.AsyncClient() as client:
        tasks = [fetch_and_extract_content(client, url) for url in urls if url]
        results = await asyncio.gather(*tasks)

    successful_sources = [source for source in results if source is not None]

    log.info(f"Успешно обработано {len(successful_sources)} источников.")
    return [source.dict() for source in successful_sources]
