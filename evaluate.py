"""
evaluate.py
GPT 기반 RAG 품질 평가 (RAGAS 직접 구현)
실행: python evaluate.py
"""

import os
import csv
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

# ── 설정 ──────────────────────────────────────────────
CHROMA_DIR      = "vectorstore/chroma_db"
COLLECTION_NAME = "nutrition"
TOP_K           = 6  # ✅ 4→6으로 늘려서 더 넓게 검색

client = OpenAI()

# ✅ 실제 PDF에 있는 식품으로 테스트 케이스 수정
TEST_CASES = [
    {
        "question": "가래떡 100g의 열량은 얼마야?",
        "ground_truth": "가래떡 100g의 열량은 195kcal입니다."
    },
    {
        "question": "닭가슴살샐러드 단백질 함량은?",
        "ground_truth": "닭가슴살샐러드 100g의 단백질 함량은 7.2g입니다."
    },
    {
        "question": "브로콜리볶음 칼로리는?",
        "ground_truth": "브로콜리볶음 100g의 열량은 51kcal로 칼로리가 낮은 편입니다."
    },
    {
    "question": "무나물 나트륨 함량이 얼마야?",
    "ground_truth": "무나물 100g의 나트륨 함량은 352.17mg입니다."
    },
    {
        "question": "북어채무침 단백질이 얼마나 돼?",
        "ground_truth": "북어채무침은 단백질 함량이 높은 음식입니다."
    },
]
# ──────────────────────────────────────────────────────


def load_retriever():
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    Settings.llm = LlamaOpenAI(model="gpt-4o-mini", temperature=0)
    chroma_client     = chromadb.PersistentClient(path=CHROMA_DIR)
    chroma_collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
    vector_store      = ChromaVectorStore(chroma_collection=chroma_collection)
    index             = VectorStoreIndex.from_vector_store(vector_store)
    return index.as_retriever(similarity_top_k=TOP_K)


def generate_answer(question, context):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": (
                "당신은 식품 영양성분 전문 챗봇입니다. "
                "참고 문서를 바탕으로 정확하게 답변하세요. "
                "없는 정보는 만들지 마세요."
            )},
            {"role": "user", "content": f"[참고 문서]\n{context}\n\n[질문]\n{question}"},
        ]
    )
    return response.choices[0].message.content.strip()


def gpt_score(prompt):
    """GPT에게 점수 요청 → 0~1 float 반환"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )
    try:
        return min(1.0, max(0.0, float(response.choices[0].message.content.strip())))
    except:
        return 0.5


def score_faithfulness(answer, context):
    return gpt_score(f"""답변이 참고 문서에만 근거하고 있는지 평가하세요.
없는 내용을 만들어냈다면 낮은 점수를 주세요.

[참고 문서]{context[:1000]}
[답변]{answer}

0.0~1.0 숫자만 출력하세요.""")


def score_answer_relevancy(question, answer):
    return gpt_score(f"""답변이 질문에 얼마나 관련있고 적절한지 평가하세요.

[질문]{question}
[답변]{answer}

0.0~1.0 숫자만 출력하세요.""")


def score_context_precision(question, context):
    return gpt_score(f"""검색된 문서가 질문에 답하기 위해 얼마나 정확한지 평가하세요.

[질문]{question}
[검색된 문서]{context[:1000]}

0.0~1.0 숫자만 출력하세요.""")


def score_context_recall(question, context, ground_truth):
    return gpt_score(f"""정답 도출에 필요한 정보가 검색된 문서에 충분히 있는지 평가하세요.

[질문]{question}
[정답]{ground_truth}
[검색된 문서]{context[:1000]}

0.0~1.0 숫자만 출력하세요.""")


def main():
    print("=" * 55)
    print("📊 RAG 품질 평가 시작 (GPT 기반 RAGAS 구현)")
    print("=" * 55)

    retriever = load_retriever()
    results   = []

    print(f"\n🔍 테스트 케이스 실행 중... (TOP_K={TOP_K})\n")

    for i, tc in enumerate(TEST_CASES):
        print(f"[{i+1}/{len(TEST_CASES)}] {tc['question']}")

        nodes   = retriever.retrieve(tc["question"])
        context = "\n\n".join(node.get_content() for node in nodes)
        answer  = generate_answer(tc["question"], context)

        print(f"  답변: {answer[:80]}...")

        f  = score_faithfulness(answer, context)
        ar = score_answer_relevancy(tc["question"], answer)
        cp = score_context_precision(tc["question"], context)
        cr = score_context_recall(tc["question"], context, tc["ground_truth"])

        print(f"  Faithfulness: {f:.2f} | Relevancy: {ar:.2f} | Precision: {cp:.2f} | Recall: {cr:.2f}\n")

        results.append({
            "question":          tc["question"],
            "answer":            answer,
            "ground_truth":      tc["ground_truth"],
            "faithfulness":      f,
            "answer_relevancy":  ar,
            "context_precision": cp,
            "context_recall":    cr,
        })

    # 평균 계산
    avg_f  = sum(r["faithfulness"]      for r in results) / len(results)
    avg_ar = sum(r["answer_relevancy"]  for r in results) / len(results)
    avg_cp = sum(r["context_precision"] for r in results) / len(results)
    avg_cr = sum(r["context_recall"]    for r in results) / len(results)
    avg    = (avg_f + avg_ar + avg_cp + avg_cr) / 4

    print("=" * 55)
    print("📊 최종 평가 결과")
    print("=" * 55)
    print(f"  Faithfulness   (충실도) : {avg_f:.4f}  {'█' * int(avg_f * 20)}")
    print(f"  Answer Relevancy (관련성): {avg_ar:.4f}  {'█' * int(avg_ar * 20)}")
    print(f"  Context Precision (정밀도): {avg_cp:.4f}  {'█' * int(avg_cp * 20)}")
    print(f"  Context Recall  (재현율): {avg_cr:.4f}  {'█' * int(avg_cr * 20)}")
    print(f"\n  평균 점수               : {avg:.4f}")
    print("=" * 55)

    # CSV 저장
    with open("ragas_results.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print("\n✅ 결과가 ragas_results.csv에 저장됐어요!")
    print("🎉 평가 완료!")


if __name__ == "__main__":
    main()