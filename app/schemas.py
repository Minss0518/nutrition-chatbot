"""
schemas.py
FastAPI 요청/응답 데이터 모델 정의
"""

from pydantic import BaseModel
from typing import List


class ChatRequest(BaseModel):
    question: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "닭가슴살 100g의 단백질 함량이 얼마나 돼?"
            }
        }
    }


class SourceDocument(BaseModel):
    page: int
    content: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
