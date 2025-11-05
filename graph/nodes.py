import re
import json
import logging
from typing import List
from .state import MarketAnalysisState
from services.llm_factory import searcher_llm, summarizer_llm, reasoner_llm
from services.web_search import search_and_scrape
import asyncio
from datetime import date
from schemas import Source, Fact
from config import CHUNK_SIZE_SUMMARIZER

log = logging.getLogger(__name__)

async def searcher_node(state: MarketAnalysisState) -> dict:
    log.info(f"--- Вход в SEARCHER (Тема: {state['topic']}) ---")
    
    prompt = f"""
Сегодня {date.today()}.
Ты — помощник-исследователь. Твоя задача — придумать 3 разнообразных поисковых запроса для Google, 
чтобы всесторонне изучить тему: '{state['topic']}'.

Верни ответ в виде JSON списка строк. Ответ должен быть в формате JSON-массива запросов. Не нужно никаких рассуждений и лишнего текста, только JSON-массив.
Пример ответа: ["запрос 1", "запрос 2", "запрос 3"]
"""
    
    response = await searcher_llm.ainvoke(prompt)
    try:
        queries = json.loads(response.content)
    except json.JSONDecodeError:
        log.warning("Не удалось распарсить JSON с поисковыми запросами. Используется тема как единственный запрос.")
        queries = [state['topic']]
    
    log.info(f"Сгенерированные поисковые запросы: {queries}")

    tasks = [search_and_scrape.ainvoke(q) for q in queries]
    results_from_tasks = await asyncio.gather(*tasks)
    
    all_sources_dict = {}
    for source_list in results_from_tasks:
        for source_data in source_list:
            if source_data['url'] not in all_sources_dict:
                all_sources_dict[source_data['url']] = Source(**source_data)
    
    unique_sources = list(all_sources_dict.values())
    log.info(f"Найдено {len(unique_sources)} уникальных релевантных источников.")
    return {"search_queries": queries, "sources": unique_sources}

async def summarizer_node(state: MarketAnalysisState) -> dict:
    log.info("--- Вход в узел SUMMARIZER ---")
    
    sources = state['sources']
    topic = state['topic']
    if not sources:
        return {"key_facts": []}

    all_facts: List[Fact] = []
    for i in range(0, len(sources), CHUNK_SIZE_SUMMARIZER):
        chunk = sources[i:i + CHUNK_SIZE_SUMMARIZER]
        
        chunk_content = "\n\n---\n\n".join(
            f"ИСТОЧНИК URL: {source.url}\nСОДЕРЖИМОЕ:\n{source.content}" for source in chunk
        )
        
        log.info(f"Анализ группы из {len(chunk)} источников...")

        prompt = f"""
Ты — высококлассный аналитик. Твоя задача — проанализировать текст из нескольких источников и извлечь 3-5 САМЫХ ВАЖНЫХ фактов, которые **напрямую относятся к теме: '{topic}'**.

ПРАВИЛА:
1.  **СТРОГАЯ РЕЛЕВАНТНОСТЬ:** Извлекай факты, только если они напрямую связаны с темой '{topic}'. Игнорируй любую побочную информацию, даже если она интересна сама по себе.
2.  **КАЧЕСТВО > КОЛИЧЕСТВО:** Лучше 2 сильных, релевантных факта, чем 5 слабых.
3.  **ИГНОРИРУЙ МУСОР:** Полностью игнорируй нерелевантную информацию (рекламу, меню сайта, информацию о cookie, тексты на других языках). Если вся группа источников нерелевантна теме, верни пустой массив.
4.  **УНИКАЛЬНОСТЬ:** Не повторяй один и тот же факт из разных источников. Сформулируй его один раз.
5.  **ОБЯЗАТЕЛЬНАЯ ССЫЛКА:** Для КАЖДОГО факта укажи URL наиболее подходящего источника.
6.  **ОБЯЗАТЕЛЬНАЯ ССЫЛКА:** Для КАЖДОГО факта укажи дату публикации в формате DD MM YY если возможно определить иначе "".
7.  **СТРОГИЙ JSON:** Ответ должен быть в формате JSON-массива объектов с ключами "fact", "source_url" и "published_date".

Текст для анализа:
---
{chunk_content}
---
"""
        try:
            response = await summarizer_llm.ainvoke(prompt)
            match = re.search(r'\[.*\]', response.content, re.DOTALL)
            if match:
                facts_from_chunk = json.loads(match.group(0))
                for fact_data in facts_from_chunk:
                    all_facts.append(Fact(**fact_data))
            
        except (json.JSONDecodeError, TypeError) as e:
            log.warning(f"Не удалось извлечь факты из группы источников: {e}")
            continue
            
    log.info(f"Всего извлечено качественных фактов: {len(all_facts)}")
    return {"key_facts": all_facts}

async def reasoner_node(state: MarketAnalysisState) -> dict:
    log.info("--- Вход в узел REASONER ---")

    facts_for_prompt = []
    for fact in state['key_facts']:
        facts_for_prompt.append({
            "fact": fact.fact,
            "source_url": fact.source_url,
            "published_date": fact.published_date
        })

    facts_json = json.dumps(facts_for_prompt, ensure_ascii=False, indent=2)

    prompt = f"""
Ты — опытный бизнес-аналитик. Перед тобой список фактов, где каждый факт имеет ссылку на свой источник и, возможно, дату публикации.
Твоя задача — написать глубокий аналитический вывод в формате Markdown.

ПРАВИЛА:
1.  Синтезируй информацию, а не просто перечисляй факты.
2.  Когда ты упоминаешь факт, ты **ОБЯЗАН** поставить на него ссылку с датой (если она есть).
3.  Используй синтаксис Markdown: `[утверждение](URL) (Опубликовано: YYYY-MM-DD)`.
4.  Твой вывод должен быть структурирован: общая оценка, возможности, риски и итоговый вывод (The Bottom Line).

Пример цитирования:
"Компания X анонсировала новый продукт [согласно пресс-релизу](https://example.com/pr-123) (Опубликовано: 2025-10-31), что может усилить ее позиции на рынке."

Список фактов в формате JSON:
---
{facts_json}
---
"""
    
    response = await reasoner_llm.ainvoke(prompt)
    final_analysis = response.content
    log.info("Финальный анализ с датами и цитатами сгенерирован.")
    
    return {"final_analysis": final_analysis}