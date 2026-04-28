from dotenv import load_dotenv
import os
load_dotenv()

# ✅ LangSmith 설정
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "false")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "nutrition-chatbot")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import asyncio
import json

from app.schemas import ChatRequest, ChatResponse, SourceDocument
from app.chain import load_chain, format_history, format_history_text

rag_chain = None
rag_retriever = None
rewrite_and_retrieve = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_chain, rag_retriever, rewrite_and_retrieve
    print("🚀 RAG 체인 초기화 중...")
    try:
        rag_chain, rag_retriever, rewrite_and_retrieve = load_chain()
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

# ✅ React 빌드 파일 서빙
FRONTEND_DIST = "nutrition-frontend/dist"
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=f"{FRONTEND_DIST}/assets"), name="assets")

@app.get("/")
def root():
    # 빌드 파일 있으면 React 앱 서빙, 없으면 API 상태 반환
    index_path = f"{FRONTEND_DIST}/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "식품 영양성분 챗봇 API 🥗", "status": "running"}

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "chain_loaded": rag_chain is not None,
    }

def parse_source_nodes(nodes):
    sources = []
    seen = set()
    for node in nodes:
        food_name = node.metadata.get("식품명", "")
        content_preview = node.get_content()[:200]
        key = content_preview[:50]
        if key not in seen:
            seen.add(key)
            sources.append(SourceDocument(page=0, content=content_preview))
    return sources

def parse_source_nodes_dict(nodes):
    sources = []
    seen = set()
    for node in nodes:
        food_name = node.metadata.get("식품명", "")
        content_preview = node.get_content()[:200]
        key = content_preview[:50]
        if key not in seen:
            seen.add(key)
            sources.append({"food_name": food_name, "content": content_preview})
    return sources


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="RAG 체인이 초기화되지 않았습니다.")
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="질문을 입력해주세요.")
    try:
        history_raw = [m.dict() for m in request.history]
        history = format_history(history_raw)
        history_text = format_history_text(history_raw)

        retrieved = rewrite_and_retrieve({
            "question": request.question,
            "history": history,
            "history_text": history_text,
        })

        answer = rag_chain.invoke(retrieved)
        source_nodes = rag_retriever.retrieve(retrieved["rewritten_question"])
        sources = parse_source_nodes(source_nodes)

        return ChatResponse(answer=answer, sources=sources)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"답변 생성 중 오류 발생: {str(e)}")


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="RAG 체인이 초기화되지 않았습니다.")
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="질문을 입력해주세요.")

    async def generate():
        try:
            history_raw = [m.dict() for m in request.history]
            history = format_history(history_raw)
            history_text = format_history_text(history_raw)

            retrieved = rewrite_and_retrieve({
                "question": request.question,
                "history": history,
                "history_text": history_text,
            })

            rewrite_data = json.dumps({
                "type": "rewrite",
                "content": retrieved["rewritten_question"]
            }, ensure_ascii=False)
            yield f"data: {rewrite_data}\n\n"

            source_nodes = rag_retriever.retrieve(retrieved["rewritten_question"])
            sources = parse_source_nodes_dict(source_nodes)

            async for chunk in rag_chain.astream(retrieved):
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
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

# ✅ React 라우터 지원 (새로고침해도 React 앱 유지)
@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    index_path = f"{FRONTEND_DIST}/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Not found")