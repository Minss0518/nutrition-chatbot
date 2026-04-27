"""
ingest.py (Marker 버전)
PDF를 Marker로 변환 후 식품별 텍스트로 파싱해서 ChromaDB에 저장

변경사항:
  - XLSX → PDF (식품영양성분_자료집_2020__통합본.pdf)
  - pandas → Marker + pdfplumber
  - 식품명, 영양성분표, 조리방법 구조적으로 파싱
"""

import os
import re
import pdfplumber
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

# ── 설정 ──────────────────────────────────────────────
PDF_PATH   = "data/식품영양성분_자료집_2020__통합본.pdf"
CHROMA_DIR = "vectorstore/chroma_db"
COLLECTION_NAME = "nutrition"

# 핵심 영양성분만 추출 (RAG 품질 향상용)
KEY_NUTRIENTS = [
    "열량 (kcal)",
    "탄수화물 (g)",
    "단백질 (g)",
    "지방 (g)",
    "식이섬유 (g)",
    "수분 (g)",
    "콜레스테롤 (mg)",
    "포화지방 (g)",
    "트랜스지방 (g)",
    "당류 (g)",
    "나트륨 (mg)",
    "칼륨 (mg)",
    "칼슘 (mg)",
    "철 (mg)",
    "인 (mg)",
    "마그네슘 (mg)",
    "아연 (mg)",
    "비타민 C (mg)",
    "레티놀 (μg)",
    "비타민 D (μg)",
]
# ──────────────────────────────────────────────────────


def extract_food_name(tables: list) -> str:
    """표 1에서 식품명 추출 (예: '깨송편\n002' → '깨송편')"""
    if not tables:
        return ""
    first_table = tables[0]
    for row in first_table:
        for cell in row:
            if cell and cell.strip():
                # 숫자 코드 제거 (예: '\n002')
                name = re.sub(r"\n\d+$", "", cell.strip())
                name = name.strip()
                if name:
                    return name
    return ""


def extract_nutrients(tables: list) -> dict:
    """표 2에서 영양성분 추출 → {영양성분명: 값(100g 기준)} 딕셔너리"""
    nutrients = {}
    if len(tables) < 2:
        return nutrients

    nutrient_table = tables[1]  # 두 번째 표가 영양성분 표
    # 표 구조: [영양성분명, 값1, 값2, 영양성분명, 값1, 값2, ...]
    # 3열씩 묶여있는 구조 (일반성분 / 지방산 / 무기질)
    for row in nutrient_table:
        # 한 행에 3개 그룹이 있음
        groups = [
            (row[0], row[1]) if len(row) > 1 else (None, None),
            (row[3], row[4]) if len(row) > 4 else (None, None),
            (row[6], row[7]) if len(row) > 7 else (None, None),
        ]
        for name, value in groups:
            if name and value and name.strip() not in ("", "None"):
                # 줄바꿈 정리 (예: '비타민 B\n1 (mg)' → '비타민 B1 (mg)')
                clean_name = re.sub(r"\s+", " ", str(name)).strip()
                clean_val = str(value).strip()
                if clean_name and clean_val not in ("None", ""):
                    nutrients[clean_name] = clean_val

    return nutrients


def extract_recipe(tables: list) -> str:
    """표 3에서 조리방법 텍스트 추출"""
    if len(tables) < 3:
        return ""
    recipe_table = tables[2]
    texts = []
    for row in recipe_table:
        for cell in row:
            if cell and str(cell).strip() not in ("", "None"):
                texts.append(str(cell).strip())
    return " ".join(texts)[:500]  # 너무 길면 잘라냄


def build_document(food_name: str, nutrients: dict, recipe: str) -> Document:
    """식품 정보를 RAG에 적합한 텍스트 Document로 변환"""
    lines = [f"식품명: {food_name}"]

    # 핵심 영양성분 먼저
    lines.append("\n[핵심 영양성분 - 100g 기준]")
    for key in KEY_NUTRIENTS:
        # 표에서 뽑은 키와 매칭 (공백 차이 있을 수 있어서 유연하게)
        for n_key, n_val in nutrients.items():
            if key.replace(" ", "") in n_key.replace(" ", ""):
                lines.append(f"  {key}: {n_val}")
                break

    # 나머지 영양성분
    extra = {k: v for k, v in nutrients.items()
             if not any(key.replace(" ", "") in k.replace(" ", "") for key in KEY_NUTRIENTS)}
    if extra:
        lines.append("\n[상세 영양성분]")
        for k, v in list(extra.items())[:20]:  # 너무 많으면 20개만
            lines.append(f"  {k}: {v}")

    # 조리방법 (있으면)
    if recipe:
        lines.append(f"\n[조리방법 요약]\n  {recipe[:200]}")

    return Document(
        page_content="\n".join(lines),
        metadata={"식품명": food_name}
    )


def load_pdf(path: str) -> list[Document]:
    """PDF 전체를 파싱해서 식품별 Document 리스트 반환"""
    print(f"📄 PDF 로딩 중: {path}")

    docs = []
    failed = 0

    with pdfplumber.open(path) as pdf:
        total = len(pdf.pages)
        print(f"   총 {total}페이지")

        for i, page in enumerate(pdf.pages):
            try:
                tables = page.extract_tables()

                # 식품 페이지 판별: 표가 3개 이상이고 식품명이 있는 페이지
                if len(tables) < 2:
                    continue

                food_name = extract_food_name(tables)
                if not food_name:
                    continue

                nutrients = extract_nutrients(tables)
                recipe    = extract_recipe(tables)

                if not nutrients:
                    continue

                doc = build_document(food_name, nutrients, recipe)
                docs.append(doc)

                if (i + 1) % 50 == 0:
                    print(f"   {i+1}/{total} 페이지 처리 중... ({len(docs)}개 식품)")

            except Exception as e:
                failed += 1
                continue

    print(f"\n   ✅ 총 {len(docs)}개 식품 문서 생성 완료")
    if failed:
        print(f"   ⚠️  {failed}개 페이지 파싱 실패 (건너뜀)")
    return docs


def save_to_chroma(docs: list[Document]):
    """문서를 임베딩 후 ChromaDB에 저장"""
    print("\n🔢 임베딩 생성 및 ChromaDB 저장 중...")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
    )
    split_docs = splitter.split_documents(docs)
    print(f"   총 {len(split_docs)}개 청크 생성")

    # 기존 vectorstore 삭제 후 재생성
    if os.path.exists(CHROMA_DIR):
        import shutil
        shutil.rmtree(CHROMA_DIR)
        print("   기존 ChromaDB 삭제 완료")

    vectorstore = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
    )
    print(f"   ✅ ChromaDB 저장 완료! ({CHROMA_DIR})")
    return vectorstore


def main():
    if not os.path.exists(PDF_PATH):
        print(f"❌ 파일을 찾을 수 없습니다: {PDF_PATH}")
        print(f"   PDF 파일을 data/ 폴더에 넣어주세요.")
        return

    print("=" * 50)
    print("🍎 식품영양성분 챗봇 - PDF 인제스트 (Marker 버전)")
    print("=" * 50)

    docs = load_pdf(PDF_PATH)

    if not docs:
        print("❌ 파싱된 문서가 없습니다. PDF 구조를 확인해주세요.")
        return

    # 샘플 출력
    print("\n📋 샘플 문서 (첫 번째 식품):")
    print("-" * 40)
    print(docs[0].page_content[:400])
    print("-" * 40)

    save_to_chroma(docs)

    print("\n🎉 완료! 이제 서버를 실행하세요:")
    print("   uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
