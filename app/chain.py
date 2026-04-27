import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

CHROMA_DIR = "vectorstore/chroma_db"
COLLECTION_NAME = "nutrition"
TOP_K = 4

# ✅ 대화 히스토리를 포함한 프롬프트
SYSTEM_PROMPT = """
당신은 식품 영양성분 전문 챗봇입니다.
아래 제공된 참고 문서를 바탕으로 사용자의 질문에 정확하고 친절하게 답변해주세요.

참고 문서에 관련 정보가 없다면, "해당 정보를 찾을 수 없습니다"라고 솔직하게 말해주세요.
절대 없는 정보를 만들어내지 마세요.
이전 대화 내용을 참고하여 자연스럽게 이어서 답변해주세요.

[참고 문서]
{context}
"""


def format_history(history: list) -> list:
    """프론트에서 받은 히스토리 → LangChain 메시지 형식으로 변환"""
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["text"]))
        elif msg["role"] == "bot":
            messages.append(AIMessage(content=msg["text"]))
    return messages


def load_chain():
    if not os.path.exists(CHROMA_DIR):
        raise FileNotFoundError(
            f"ChromaDB를 찾을 수 없습니다: {CHROMA_DIR}\n"
            "먼저 ingest.py를 실행해주세요: python ingest.py"
        )

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K},
    )

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        streaming=True,
    )

    # ✅ 히스토리 포함 프롬프트
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ])

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # ✅ 히스토리 + 질문 + 컨텍스트를 받는 체인
    chain = (
        {
            "context": lambda x: format_docs(retriever.invoke(x["question"])),
            "question": lambda x: x["question"],
            "history": lambda x: x["history"],
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever