import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from schemas import AnalysisRequest, AnalysisResponse
from graph.builder import analyst_graph_app

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("FastAPIApp")

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Сервис запущен.")
    yield
    log.info("Сервис остановлен.")

app = FastAPI(
    title="API аналитика",
    description="API для анализа рыночных трендов с помощью AI-агентов.",
    version="1.0.0",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_topic(request: AnalysisRequest):
    log.info(f"Получен запрос на анализ темы: '{request.topic}'")
    
    initial_state = {"topic": request.topic}
    
    try:
        final_state = await analyst_graph_app.ainvoke(initial_state)
        
        log.info(f"Анализ темы '{request.topic}' успешно завершен.")
        
        return AnalysisResponse(
            topic=request.topic,
            key_facts=final_state.get('key_facts', 'Не удалось извлечь факты.'),
            final_analysis=final_state.get('final_analysis', 'Не удалось сформировать вывод.')
        )
    except Exception as e:
        log.error(f"Критическая ошибка в процессе анализа темы '{request.topic}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {e}")

@app.get("/health", summary="Проверка состояния сервиса")
def health_check():
    return {"status": "ok"}

