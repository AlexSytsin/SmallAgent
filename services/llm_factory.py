from langchain_openai import ChatOpenAI
from config import GROQ_API_KEY, GROQ_BASE_URL, SEARCHER_MODEL, SUMMARIZER_MODEL, REASONER_MODEL

def get_llm(model_name: str, temperature: float = 0.0) -> ChatOpenAI:
    """Фабричная функция для создания экземпляров ChatOpenAI для Groq."""
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL
    )

searcher_llm = get_llm(SEARCHER_MODEL)
summarizer_llm = get_llm(SUMMARIZER_MODEL)
reasoner_llm = get_llm(REASONER_MODEL)
