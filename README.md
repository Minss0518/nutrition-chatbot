# 🥗 식품 영양성분 챗봇

식품의약품안전처 영양성분 PDF를 기반으로 한 **RAG(검색 증강 생성) 챗봇**입니다.  
LangChain + ChromaDB + FastAPI로 구성되어 있습니다.

## 📁 프로젝트 구조

```
nutrition-chatbot/
├── data/
│   └── nutrition.pdf          # 식품영양성분 PDF (직접 넣어주세요)
├── vectorstore/
│   └── chroma_db/             # ChromaDB 자동 생성됨
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI 서버
│   ├── chain.py               # LangChain RAG 체인
│   └── schemas.py             # 요청/응답 모델
├── ingest.py                  # PDF → 벡터DB 변환 스크립트
├── requirements.txt
├── .env.example
└── README.md
```

## ⚙️ 설치 및 실행

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정
```bash
cp .env.example .env
# .env 파일에 OpenAI API 키 입력
```

### 3. PDF 파일 배치
```
data/ 폴더에 nutrition.pdf 파일을 넣어주세요.
```

### 4. PDF → ChromaDB 변환 (최초 1회)
```bash
python ingest.py
```

### 5. 서버 실행
```bash
uvicorn app.main:app --reload
```

### 6. API 테스트
- Swagger UI: http://localhost:8000/docs
- 헬스 체크: http://localhost:8000/health

## 📡 API 명세

### POST /chat
**요청**
```json
{
  "question": "닭가슴살 100g의 단백질 함량이 얼마나 돼?"
}
```

**응답**
```json
{
  "answer": "닭가슴살 100g에는 약 23g의 단백질이 포함되어 있습니다...",
  "sources": [
    {
      "page": 42,
      "content": "닭가슴살(생것) 영양성분 ..."
    }
  ]
}
```

## 🛠️ 기술 스택
- **LangChain** - RAG 파이프라인
- **ChromaDB** - 벡터 데이터베이스
- **OpenAI** - 임베딩(text-embedding-3-small) + LLM(gpt-4o-mini)
- **FastAPI** - REST API 서버
- **PyPDF** - PDF 파싱
