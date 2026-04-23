import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

CHROMA_DIR = "vectorstore/chroma_db"
COLLECTION_NAME = "nutrition"
TOP_K = 4

PROMPT_TEMPLATE = """
당신은 식품 영양성분 전문 챗봇입니다.
아래 제공된 참고 문서를 바탕으로 사용자의 질문에 정확하고 친절하게 답변해주세요.

참고 문서에 관련 정보가 없다면, "해당 정보를 찾을 수 없습니다"라고 솔직하게 말해주세요.
절대 없는 정보를 만들어내지 마세요.

[참고 문서]
{context}

[사용자 질문]
{question}

[답변]
"""

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
    )

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=PROMPT_TEMPLATE,
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever