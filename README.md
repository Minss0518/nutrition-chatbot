# 🥗 식품영양성분 챗봇 (nutrition-chatbot)

식품의약품안전처 공공데이터 기반 RAG 챗봇입니다.
560페이지 분량의 식품영양성분 PDF를 직접 파싱하여 식품별 영양정보를 정확하게 답변합니다.

---

## 📌 프로젝트 소개

> "닭가슴살 100g 단백질이 얼마야?" → "그럼 지방은?" 처럼 이전 대화를 기억하며 자연스럽게 이어서 답변합니다.

- **데이터**: 식품의약품안전처 식품영양성분 자료집 2020 (560페이지, 약 280개 식품)
- **핵심 기술**: LangChain RAG + ChromaDB + FastAPI + React
- **특징**: PDF 직접 파싱 → 스트리밍 답변 → 대화 메모리

---

## 🛠️ 기술 스택

| 구분 | 기술 |
|---|---|
| 백엔드 | Python 3.11, FastAPI, LangChain |
| AI 모델 | OpenAI gpt-4o-mini, text-embedding-3-small |
| 벡터 DB | ChromaDB |
| PDF 파싱 | pdfplumber |
| 프론트엔드 | React + Vite |
| 스트리밍 | Server-Sent Events (SSE) |

---

## 🚀 실행 방법

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
# .env 파일 생성
OPENAI_API_KEY=your_openai_api_key
```

### 3. PDF 준비

```
nutrition-chatbot/
└── data/
    └── 식품영양성분+자료집(2020)_통합본.pdf  ← 여기에 넣기
```

> 식품안전나라(www.foodsafetykorea.go.kr) 또는 식품의약품안전처에서 다운로드

### 4. 데이터 인제스트 (ChromaDB 생성)

```bash
python ingest.py
```

### 5. 서버 실행

```bash
# 터미널 1 - 백엔드
uvicorn app.main:app --reload

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
│   ├── chain.py        # LangChain RAG 체인 (메모리 포함)
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
└── requirements.txt
```

---

## 🔄 개발 과정 & 개선 이력

### v1.0 - XLSX 기반 챗봇
- 처음에는 PDF 파싱이 불가능하다고 판단 → XLSX 데이터로 우회
- pandas로 행 단위 읽기 → ChromaDB 저장
- 19,208개 청크 생성

### v2.0 - PDF 직접 파싱으로 전환
- PDF 구조 분석 결과 Adobe InDesign 디지털 PDF로 확인 (스캔본 아님)
- pdfplumber로 표 구조 직접 파싱 성공
- 식품명 / 핵심 영양성분 / 상세 영양성분 / 조리방법으로 구조화
- XLSX 대비 조리방법 정보 추가 확보

### v2.1 - 스트리밍 답변 추가
- 기존: 답변 완성 후 한 번에 출력
- 개선: Server-Sent Events(SSE)로 토큰 단위 실시간 출력
- 백엔드: `/chat/stream` 엔드포인트 추가
- 프론트: `ReadableStream` API로 청크 단위 수신

### v2.2 - 대화 메모리 추가
- 기존: 매 질문이 독립적 → "그럼 단백질은?" 같은 질문 이해 불가
- 개선: 대화 히스토리를 프론트에서 백엔드로 전달
- `MessagesPlaceholder`로 이전 대화 컨텍스트 유지
- "그럼 단백질은?" → 직전 식품 맥락 이해하여 정확히 답변

---

## 📊 타 프로젝트와의 비교

> 근로기준법 챗봇 → 부동산 법률 챗봇 → 식품영양성분 챗봇 순으로 개발하며 각 프로젝트에서 발견한 문제를 다음 프로젝트에서 개선했습니다.

| 기능 | 근로기준법 챗봇 | 부동산 법률 챗봇 | 식품영양성분 챗봇 |
|---|---|---|---|
| 데이터 소스 | PDF 1개 | PDF 3개 통합 | PDF 560페이지 |
| PDF 파싱 | 기본 (pypdf) | Marker AI 모델 | pdfplumber (표 구조 파싱) |
| 스트리밍 | ❌ | ✅ | ✅ |
| 대화 메모리 | ❌ | ✅ | ✅ |
| 질문 리라이팅 | ❌ | ✅ | ❌ |
| 데이터 유형 | 텍스트 문서 | 텍스트 문서 | 표 + 텍스트 혼합 |
| 특이점 | RAG 기초 구현 | 멀티 PDF + 고도화 | 정형 데이터 RAG |

### 식품영양성분 챗봇만의 차별점

1. **표 데이터 RAG**: 일반 텍스트가 아닌 영양성분 표를 구조화하여 RAG에 활용
2. **PDF 직접 분석**: 단순 텍스트 추출이 아닌 표 구조(행/열)를 인식하여 파싱
3. **데이터 소스 전환 경험**: XLSX 우회 → PDF 직접 파싱으로 전환한 문제 해결 과정

---

## ⚠️ 해결한 주요 문제들

| 문제 | 원인 | 해결 |
|---|---|---|
| PDF 파싱 불가 | 처음엔 표+그림 혼합이라 판단 | PDF 구조 분석 후 pdfplumber로 표 직접 추출 |
| XLSX → PDF 전환 | 데이터 소스 변경 | ingest.py 전면 재작성 |
| venv 파일 변경 감지 | uvicorn이 venv 내부 파일 감시 | `--reload-exclude venv` 옵션 적용 |
| ChromaDB 삭제 권한 오류 | Windows 파일 잠금 | 서버 종료 후 탐색기에서 직접 삭제 |

---

## 💬 면접 포인트

> "처음엔 PDF의 표 구조를 파싱하지 못해 XLSX로 우회했습니다. 이후 PDF 구조를 직접 분석해보니 디지털 PDF였고, pdfplumber로 표 데이터를 정확하게 추출할 수 있었습니다. 단순 텍스트가 아닌 정형 데이터를 RAG에 활용한 경험이며, 스트리밍과 대화 메모리까지 추가하여 UX를 개선했습니다."

면접용 멘트

"세 프로젝트에서 PDF 파싱 방법을 각각 다르게 적용했습니다. pypdf는 텍스트 위주 문서에, Marker AI는 이미지와 표가 혼합된 복잡한 문서에, pdfplumber는 영양성분표처럼 표 구조가 중요한 데이터에 사용했습니다. PDF 유형에 따라 적합한 도구를 선택하는 경험을 쌓았습니다."