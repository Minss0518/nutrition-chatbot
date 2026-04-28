import os
os.environ["OPENAI_API_KEY"] = "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"
from dotenv import load_dotenv


from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
from langchain_core.messages import HumanMessage, AIMessage
import chromadb

load_dotenv()

import os
print(f"🔑 OPENAI_API_KEY 앞 10자: {os.getenv('OPENAI_API_KEY', 'None')[:10]}")

CHROMA_DIR      = "vectorstore/chroma_db"
COLLECTION_NAME = "nutrition"
TOP_K           = 6  # ✅ 4→6으로 늘림

# ✅ 개선된 리라이팅 프롬프트
REWRITE_PROMPT = """당신은 식품 영양성분 검색 전문가입니다.
아래 대화 히스토리와 사용자 질문을 보고, 벡터 DB 검색에 최적화된 질문으로 재작성하세요.

규칙:
- "그럼", "거기서", "그거" 같은 지시어를 구체적인 식품명으로 교체
- 식품명 + 영양성분명 키워드 위주로 작성
- "낮은", "높은" 같은 비교 표현은 반드시 유지
- "나트륨 낮은" → "나트륨 함량이 낮은 식품" 처럼 명확하게
- "칼로리 낮은" → "열량이 낮은 식품" 처럼 명확하게
- 재작성된 질문만 출력 (설명 없이)

[대화 히스토리]
{history}

[현재 질문]
{question}

[재작성된 검색 질문]"""

ANSWER_PROMPT = """당신은 식품 영양성분 전문 챗봇입니다.
아래 참고 문서를 바탕으로 사용자의 질문에 정확하고 친절하게 답변해주세요.

참고 문서에 정보가 없다면 "해당 정보를 찾을 수 없습니다"라고 말해주세요.
절대 없는 정보를 만들어내지 마세요.
이전 대화 내용을 참고하여 자연스럽게 이어서 답변해주세요.

[대화 히스토리]
{history}

[참고 문서]
{context}

[사용자 질문]
{question}

[답변]"""


def format_history(history: list) -> list:
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["text"]))
        elif msg["role"] == "bot":
            messages.append(AIMessage(content=msg["text"]))
    return messages


def format_history_text(history: list) -> str:
    if not history:
        return "없음"
    lines = []
    for msg in history:
        role = "사용자" if msg["role"] == "user" else "챗봇"
        lines.append(f"{role}: {msg['text']}")
    return "\n".join(lines[-6:])


def load_chain():
    if not os.path.exists(CHROMA_DIR):
        raise FileNotFoundError(
            f"ChromaDB를 찾을 수 없습니다: {CHROMA_DIR}\n"
            "먼저 ingest.py를 실행해주세요: python ingest.py"
        )

    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.2)

    chroma_client     = chromadb.PersistentClient(path=CHROMA_DIR)
    chroma_collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
    vector_store      = ChromaVectorStore(chroma_collection=chroma_collection)
    index             = VectorStoreIndex.from_vector_store(vector_store)
    retriever         = index.as_retriever(similarity_top_k=TOP_K)

    rewrite_llm = OpenAI(model="gpt-4o-mini", temperature=0)
    answer_llm  = OpenAI(model="gpt-4o-mini", temperature=0.2)

    def rewrite_question(question, history_text):
        prompt   = REWRITE_PROMPT.format(history=history_text, question=question)
        response = rewrite_llm.complete(prompt)
        return response.text.strip()

    def rewrite_and_retrieve(inputs):
        question     = inputs["question"]
        history_text = inputs["history_text"]
        history      = inputs["history"]

        rewritten = rewrite_question(question, history_text)
        print(f"\n🔄 리라이팅: '{question}' → '{rewritten}'")

        nodes   = retriever.retrieve(rewritten)
        context = "\n\n".join(node.get_content() for node in nodes)

        return {
            "context":            context,
            "question":           question,
            "history":            history,
            "history_text":       history_text,
            "rewritten_question": rewritten,
            "source_nodes":       nodes,
        }

    class AnswerChain:
        def invoke(self, inputs):
            prompt   = ANSWER_PROMPT.format(
                history=inputs["history_text"],
                context=inputs["context"],
                question=inputs["question"],
            )
            response = answer_llm.complete(prompt)
            return response.text.strip()

        async def astream(self, inputs):
            prompt   = ANSWER_PROMPT.format(
                history=inputs["history_text"],
                context=inputs["context"],
                question=inputs["question"],
            )
            response = await answer_llm.astream_complete(prompt)
            async for chunk in response:
                yield chunk.delta

    return AnswerChain(), retriever, rewrite_and_retrieve