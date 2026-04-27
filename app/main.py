from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import asyncio
import json

from app.schemas import ChatRequest, ChatResponse, SourceDocument
from app.chain import load_chain, format_history

rag_chain = None
rag_retriever = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_chain, rag_retriever
    print("🚀 RAG 체인 초기화 중...")
    try:
        rag_chain, rag_retriever = load_chain()
        print("✅ RAG 체인 준비 완료!")
    except FileNotFoundError as e:
        print(f"⚠️  경고: {e}")
    yield
    print("🛑 서버 종료")

app = FastAPI(
    title="식품 영양성분 챗봇 API",
    description="식품영양성분 PDF 기반 RAG 챗봇입니다.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "식품 영양성분 챗봇 API 🥗", "status": "running"}

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "chain_loaded": rag_chain is not None,
    }

# 기존 /chat (그대로 유지)
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="RAG 체인이 초기화되지 않았습니다.")
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="질문을 입력해주세요.")
    try:
        history = format_history([m.dict() for m in request.history])
        answer = rag_chain.invoke({"question": request.question, "history": history})

        source_docs = rag_retriever.invoke(request.question)
        sources = []
        seen = set()
        for doc in source_docs:
            page = doc.metadata.get("page", 0) + 1
            content_preview = doc.page_content[:200]
            key = content_preview[:50]
            if key not in seen:
                seen.add(key)
                sources.append(SourceDocument(page=page, content=content_preview))

        return ChatResponse(answer=answer, sources=sources)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"답변 생성 중 오류 발생: {str(e)}")


# ✅ 스트리밍 + 메모리 엔드포인트
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="RAG 체인이 초기화되지 않았습니다.")
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="질문을 입력해주세요.")

    async def generate():
        try:
            source_docs = rag_retriever.invoke(request.question)
            sources = []
            seen = set()
            for doc in source_docs:
                food_name = doc.metadata.get("식품명", "")
                content_preview = doc.page_content[:200]
                key = content_preview[:50]
                if key not in seen:
                    seen.add(key)
                    sources.append({
                        "food_name": food_name,
                        "content": content_preview,
                    })

            history = format_history([m.dict() for m in request.history])
            async for chunk in rag_chain.astream({"question": request.question, "history": history}):
                data = json.dumps({"type": "token", "content": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"
                await asyncio.sleep(0)

            data = json.dumps({"type": "sources", "content": sources}, ensure_ascii=False)
            yield f"data: {data}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            error_data = json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )