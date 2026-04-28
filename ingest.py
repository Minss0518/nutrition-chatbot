"""
ingest.py (LlamaIndex 버전)
PDF를 pdfplumber로 파싱 후 LlamaIndex + ChromaDB에 저장
"""

import os
import re
import pdfplumber
from dotenv import load_dotenv

from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

load_dotenv()

# ── 설정 ──────────────────────────────────────────────
PDF_PATH = "data/식품영양성분_자료집_2020__통합본.pdf"
CHROMA_DIR      = "vectorstore/chroma_db"
COLLECTION_NAME = "nutrition"

KEY_NUTRIENTS = [
    "열량 (kcal)", "탄수화물 (g)", "단백질 (g)", "지방 (g)",
    "식이섬유 (g)", "수분 (g)", "콜레스테롤 (mg)", "포화지방 (g)",
    "트랜스지방 (g)", "당류 (g)", "나트륨 (mg)", "칼륨 (mg)",
    "칼슘 (mg)", "철 (mg)", "인 (mg)", "마그네슘 (mg)",
    "아연 (mg)", "비타민 C (mg)", "레티놀 (μg)", "비타민 D (μg)",
]
# ──────────────────────────────────────────────────────


def extract_food_name(tables):
    if not tables:
        return ""
    for row in tables[0]:
        for cell in row:
            if cell and cell.strip():
                name = re.sub(r"\n\d+$", "", cell.strip())
                return name.strip()
    return ""


def extract_nutrients(tables):
    nutrients = {}
    if len(tables) < 2:
        return nutrients
    for row in tables[1]:
        groups = [
            (row[0], row[1]) if len(row) > 1 else (None, None),
            (row[3], row[4]) if len(row) > 4 else (None, None),
            (row[6], row[7]) if len(row) > 7 else (None, None),
        ]
        for name, value in groups:
            if name and value and str(name).strip() not in ("", "None"):
                clean_name = re.sub(r"\s+", " ", str(name)).strip()
                clean_val  = str(value).strip()
                if clean_name and clean_val not in ("None", ""):
                    nutrients[clean_name] = clean_val
    return nutrients


def extract_recipe(tables):
    if len(tables) < 3:
        return ""
    texts = []
    for row in tables[2]:
        for cell in row:
            if cell and str(cell).strip() not in ("", "None"):
                texts.append(str(cell).strip())
    return " ".join(texts)[:500]


def build_text(food_name, nutrients, recipe):
    lines = [f"식품명: {food_name}"]
    lines.append("\n[핵심 영양성분 - 100g 기준]")
    for key in KEY_NUTRIENTS:
        for nk, nv in nutrients.items():
            if key.replace(" ", "") in nk.replace(" ", ""):
                lines.append(f"  {key}: {nv}")
                break
    extra = {k: v for k, v in nutrients.items()
             if not any(key.replace(" ", "") in k.replace(" ", "") for key in KEY_NUTRIENTS)}
    if extra:
        lines.append("\n[상세 영양성분]")
        for k, v in list(extra.items())[:20]:
            lines.append(f"  {k}: {v}")
    if recipe:
        lines.append(f"\n[조리방법 요약]\n  {recipe[:200]}")
    return "\n".join(lines)


def load_pdf(path):
    print(f"📄 PDF 로딩 중: {path}")
    docs = []
    with pdfplumber.open(path) as pdf:
        total = len(pdf.pages)
        print(f"   총 {total}페이지")
        for i, page in enumerate(pdf.pages):
            try:
                tables = page.extract_tables()
                if len(tables) < 2:
                    continue
                food_name = extract_food_name(tables)
                if not food_name:
                    continue
                nutrients = extract_nutrients(tables)
                if not nutrients:
                    continue
                recipe = extract_recipe(tables)
                text = build_text(food_name, nutrients, recipe)

                # ✅ LlamaIndex Document 형식
                docs.append(Document(
                    text=text,
                    metadata={"식품명": food_name}
                ))
                if (i + 1) % 50 == 0:
                    print(f"   {i+1}/{total} 페이지 처리 중... ({len(docs)}개 식품)")
            except Exception:
                continue
    print(f"\n   ✅ 총 {len(docs)}개 식품 문서 생성 완료")
    return docs


def save_to_chroma(docs):
    print("\n🔢 임베딩 생성 및 ChromaDB 저장 중...")

    # ✅ LlamaIndex 임베딩 설정
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

    # 기존 ChromaDB 삭제 후 재생성
    if os.path.exists(CHROMA_DIR):
        import shutil
        shutil.rmtree(CHROMA_DIR)
        print("   기존 ChromaDB 삭제 완료")

    # ✅ ChromaDB 연결
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    chroma_collection = chroma_client.get_or_create_collection(COLLECTION_NAME)

    # ✅ LlamaIndex VectorStore 설정
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # ✅ 인덱스 생성 (임베딩 + 저장 한 번에)
    index = VectorStoreIndex.from_documents(
        docs,
        storage_context=storage_context,
        show_progress=True,
    )
    print(f"   ✅ ChromaDB 저장 완료! ({CHROMA_DIR})")
    return index


def main():
    if not os.path.exists(PDF_PATH):
        print(f"❌ 파일을 찾을 수 없습니다: {PDF_PATH}")
        return

    print("=" * 50)
    print("🍎 식품영양성분 챗봇 - PDF 인제스트 (LlamaIndex 버전)")
    print("=" * 50)

    docs = load_pdf(PDF_PATH)
    if not docs:
        print("❌ 파싱된 문서가 없습니다.")
        return

    print("\n📋 샘플 문서 (첫 번째 식품):")
    print("-" * 40)
    print(docs[0].text[:400])
    print("-" * 40)

    save_to_chroma(docs)

    print("\n🎉 완료! 이제 서버를 실행하세요:")
    print("   python -m uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()