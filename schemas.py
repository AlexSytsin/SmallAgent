from typing import List, Optional
from pydantic import BaseModel, Field

# --- Внутренние структуры данных ---

class Source(BaseModel):
    url: str
    content: str
    published_date: Optional[str] = None

class Fact(BaseModel):
    fact: str
    source_url: str
    published_date: Optional[str] = None

# --- Модели API ---

class AnalysisRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=150)

class AnalysisResponse(BaseModel):
    topic: str
    key_facts: List[Fact]
    final_analysis: str
