"""
schemas.py
FastAPI 요청/응답 데이터 모델 정의
"""

from pydantic import BaseModel
from typing import List


# ✅ 대화 히스토리 한 턴
class ChatMessage(BaseModel):
    role: str   # "user" or "bot"
    text: str


class ChatRequest(BaseModel):
    question: str
    history: List[ChatMessage] = []  # ✅ 대화 히스토리 추가 (기본값 빈 리스트)

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "그럼 단백질은?",
                "history": [
                    {"role": "user", "text": "닭가슴살 100g 열량이 얼마야?"},
                    {"role": "bot", "text": "닭가슴살 100g의 열량은 109kcal입니다."},
                ]
            }
        }
    }


class SourceDocument(BaseModel):
    page: int
    content: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]