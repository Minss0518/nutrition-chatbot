"""
ingest.py
XLSX 파일을 읽어서 식품별 텍스트로 변환 후 ChromaDB에 저장
"""

import os
import pandas as pd
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

XLSX_PATH = "data/nutrition.xlsx"
CHROMA_DIR = "vectorstore/chroma_db"
COLLECTION_NAME = "nutrition"

def load_xlsx(path: str):
    """XLSX를 읽어서 식품별 텍스트 문서로 변환"""
    print(f"📊 XLSX 로딩 중: {path}")
    df = pd.read_excel(path)
    print(f"   총 {len(df)}행 로드 완료")
    print(f"   컬럼 목록: {list(df.columns[:10])}...")

    docs = []
    for _, row in df.iterrows():
        # 식품명 찾기 (컬럼명이 다를 수 있어서 유연하게 처리)
        food_name = ""
        for col in df.columns:
            if "식품명" in str(col) or "음식명" in str(col):
                food_name = str(row[col])
                break

        if not food_name or food_name == "nan":
            continue

        # 행 전체를 "항목: 값" 형태의 텍스트로 변환
        text_parts = [f"식품명: {food_name}"]
        for col in df.columns:
            val = row[col]
            if pd.notna(val) and str(val) != "nan" and str(col) != "식품명":
                text_parts.append(f"{col}: {val}")

        text = "\n".join(text_parts)
        docs.append(Document(page_content=text, metadata={"식품명": food_name}))

    print(f"   총 {len(docs)}개 식품 문서 생성 완료")
    return docs


def save_to_chroma(docs):
    """문서를 임베딩 후 ChromaDB에 저장"""
    print("🔢 임베딩 생성 및 ChromaDB 저장 중...")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # 너무 많으면 청킹
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=50,
    )
    split_docs = splitter.split_documents(docs)
    print(f"   총 {len(split_docs)}개 청크 생성")

    vectorstore = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
    )
    print(f"   ✅ ChromaDB 저장 완료!")
    return vectorstore


def main():
    if not os.path.exists(XLSX_PATH):
        print(f"❌ 파일을 찾을 수 없습니다: {XLSX_PATH}")
        return

    docs = load_xlsx(XLSX_PATH)
    save_to_chroma(docs)
    print("\n🎉 완료! 서버를 실행하세요: uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()