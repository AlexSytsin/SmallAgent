import os
from dotenv import load_dotenv

load_dotenv()

# --- API ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

# --- Модели ---
SEARCHER_MODEL = "llama-3.1-8b-instant"
SUMMARIZER_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
REASONER_MODEL = "llama-3.3-70b-versatile"

# --- Константы ---
CHUNK_SIZE_SUMMARIZER = 3

required_env_vars = {
    "GROQ_API_KEY": GROQ_API_KEY,
    "GOOGLE_API_KEY": GOOGLE_API_KEY,
    "GOOGLE_CX": GOOGLE_CX
}

for var_name, var_value in required_env_vars.items():
    if not var_value:
        raise ValueError(f"Необходимо установить '{var_name}' в .env файле")
