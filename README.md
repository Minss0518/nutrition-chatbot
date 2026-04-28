# 🥗 식품영양성분 챗봇 (nutrition-chatbot)

식품의약품안전처 공공데이터 기반 RAG 챗봇입니다.
560페이지 분량의 식품영양성분 PDF를 직접 파싱하여 식품별 영양정보를 정확하게 답변합니다.

🌐 **배포 URL**: [web-production-d24fd.up.railway.app](https://web-production-d24fd.up.railway.app)

---

## 📌 프로젝트 소개

> "닭가슴살샐러드 단백질이 얼마야?" → "그럼 지방은?" 처럼 이전 대화를 기억하며 자연스럽게 이어서 답변합니다.

- **데이터**: 식품의약품안전처 식품영양성분 자료집 2020 (560페이지, 548개 식품)
- **핵심 기술**: LlamaIndex RAG + ChromaDB + FastAPI + React
- **특징**: PDF 직접 파싱 → 질문 리라이팅 → 스트리밍 답변 → 대화 메모리

---

## 🛠️ 기술 스택

| 구분 | 기술 |
|---|---|
| 백엔드 | Python 3.11, FastAPI, LlamaIndex |
| AI 모델 | OpenAI gpt-4o-mini, text-embedding-3-small |
| 벡터 DB | ChromaDB |
| PDF 파싱 | pdfplumber |
| 프론트엔드 | React + Vite |
| 스트리밍 | Server-Sent Events (SSE) |
| 모니터링 | LangSmith |
| 품질 평가 | RAGAS (GPT 기반 직접 구현) |
| 배포 | Railway |

---

## 🚀 실행 방법

### 1. 환경 설정

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
# .env 파일 생성
OPENAI_API_KEY=your_openai_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=nutrition-chatbot
```

### 3. PDF 준비

```
nutrition-chatbot/
└── data/
    └── 식품영양성분_자료집_2020_통합본.pdf
```

### 4. 데이터 인제스트

```bash
python ingest.py
```

### 5. 서버 실행

```bash
# 터미널 1 - 백엔드
python -m uvicorn app.main:app --reload

# 터미널 2 - 프론트엔드
cd nutrition-frontend
npm install
npm run dev
```

### 6. 접속

```
http://localhost:5173
```

---

## 📁 프로젝트 구조

```
nutrition-chatbot/
├── app/
│   ├── chain.py        # LlamaIndex RAG 체인 (질문 리라이팅 + 메모리)
│   ├── main.py         # FastAPI 서버 (스트리밍 엔드포인트)
│   └── schemas.py      # 요청/응답 모델 (히스토리 포함)
├── nutrition-frontend/
│   └── src/
│       ├── api/chatApi.jsx       # 스트리밍 API 호출
│       ├── hooks/useChat.jsx     # 대화 상태 관리
│       └── components/          # UI 컴포넌트
├── data/                        # PDF 파일 위치
├── vectorstore/                 # ChromaDB 저장 위치
├── ingest.py                    # PDF 파싱 → ChromaDB 저장
├── evaluate.py                  # RAGAS 품질 평가
├── Procfile                     # Railway 배포 설정
├── nixpacks.toml                # Railway 빌드 설정
└── requirements.txt
```

---

## 🔄 개발 과정 & 개선 이력

### v1.0 - XLSX 기반 챗봇
- PDF 파싱 불가 판단 → XLSX 데이터로 우회
- pandas로 행 단위 읽기 → ChromaDB 저장

### v2.0 - PDF 직접 파싱
- PDF 구조 분석 결과 디지털 PDF 확인
- pdfplumber로 표 구조 직접 파싱
- 식품명 / 핵심영양성분 / 상세영양성분 / 조리방법 구조화

### v2.1 - 스트리밍 + 대화 메모리
- SSE 기반 토큰 단위 실시간 출력
- 대화 히스토리 프론트 → 백엔드 전달
- "그럼 단백질은?" 같은 문맥 질문 이해

### v2.2 - 질문 리라이팅 + LangSmith
- 모호한 질문을 검색에 최적화된 질문으로 재작성
- LangSmith로 모든 LLM 호출 모니터링

### v2.3 - LlamaIndex 전환
- LangChain → LlamaIndex RAG 체인 전환
- VectorStoreIndex + ChromaVectorStore 활용

### v2.4 - RAGAS 품질 측정 + Railway 배포
- GPT 기반 RAGAS 직접 구현 (Faithfulness / Relevancy / Precision / Recall)
- 1차 평균 0.66 → 개선 후 0.77
- Railway 배포로 24시간 서비스 운영

---

## 📊 RAGAS 품질 평가 결과

| 지표 | 1차 | 개선 후 |
|---|---|---|
| Faithfulness (충실도) | 0.48 | 0.80 |
| Answer Relevancy (관련성) | 0.65 | 0.96 |
| Context Precision (정밀도) | 0.64 | 0.72 |
| Context Recall (재현율) | 0.53 | 0.60 |
| **평균** | **0.66** | **0.77** |

---

## 📊 타 프로젝트와의 비교

| 기능 | 근로기준법 챗봇 | 부동산 법률 챗봇 | 식품영양성분 챗봇 |
|---|---|---|---|
| 데이터 소스 | PDF 1개 | PDF 3개 통합 | PDF 560페이지 |
| PDF 파싱 | pypdf (기본) | Marker AI | pdfplumber (표 구조) |
| RAG 프레임워크 | LlamaIndex | LangChain | LlamaIndex |
| 스트리밍 | ❌ | ✅ | ✅ |
| 대화 메모리 | ❌ | ✅ | ✅ |
| 질문 리라이팅 | ❌ | ✅ | ✅ |
| RAGAS 품질 측정 | ✅ | ✅ | ✅ |
| LangSmith | ✅ | ✅ | ✅ |
| 배포 | ❌ | ❌ | ✅ Railway |

---

## ⚠️ 해결한 주요 문제들

| 문제 | 원인 | 해결 |
|---|---|---|
| PDF 파싱 불가 | 표+그림 혼합이라 판단 | PDF 구조 분석 후 pdfplumber로 표 직접 추출 |
| pyarrow DLL 차단 | Device Guard 보안 정책 | RAGAS 핵심 로직 GPT 기반으로 직접 구현 |
| Railway 환경변수 미적용 | Raw Editor 따옴표 문제 | + New Variable로 개별 입력 |
| dist 폴더 gitignore | 두 곳에서 막힘 | git add -f 강제 추가 |
| GitHub API 키 노출 차단 | 코드에 키값 하드코딩 | 키 재발급 후 환경변수로 관리 |

---

## 💬 면접 포인트

> "식품영양성분 챗봇을 LlamaIndex 기반으로 구현하고 Railway에 배포했습니다. 처음엔 PDF 파싱이 안 돼서 XLSX로 우회했는데, PDF 구조를 직접 분석해서 pdfplumber로 표 데이터를 정확하게 추출했습니다. 질문 리라이팅으로 검색 정확도를 높였고, RAGAS로 품질을 측정해 평균 0.66에서 0.77로 개선했습니다. 또한 보안 정책으로 RAGAS 라이브러리를 사용할 수 없는 환경에서 핵심 로직을 직접 구현한 경험도 있습니다."