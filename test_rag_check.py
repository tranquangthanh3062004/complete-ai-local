"""
RAG Pipeline Diagnostic — Check vector store health, document count, retrieval quality.
"""
from services.ai_rag import get_vector_store

print("=" * 60)
print("  RAG Pipeline Diagnostic")
print("=" * 60)

db = get_vector_store()
coll = db._collection
print(f"[OK] Collection: {coll.name}")
print(f"[OK] Total documents: {coll.count()}")

test_queries = [
    "tuyen xe buyt di qua Trieu Khuc Bach Khoa",
    "gia ve xe buyt Ha Noi",
    "metro Cat Linh Ha Dong",
    "di tu san bay Noi Bai ve trung tam",
    "tuyen xe buyt so 31 Bach Khoa",
]

for q in test_queries:
    print(f"\n--- Query: '{q}' ---")
    try:
        results = db.similarity_search(q, k=2)
        if results:
            for i, r in enumerate(results):
                src = r.metadata.get("source", "?")
                preview = r.page_content[:150].replace("\n", " ")
                print(f"  [{i+1}] src={src}")
                print(f"      {preview}...")
        else:
            print("  [EMPTY] No results found!")
    except Exception as e:
        print(f"  [ERROR] {e}")

print("\n" + "=" * 60)
print("  Diagnostic Complete")
print("=" * 60)
