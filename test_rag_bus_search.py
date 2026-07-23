"""
Test RAG search over local data directory for GTCC bus routes.
"""
import sys
import asyncio

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from services.ai_rag import get_vector_store, format_docs

def main():
    db = get_vector_store()
    
    queries = [
        "Tuyến xe buýt Bách Khoa",
        "Tuyến xe buýt Nguyễn Trãi Yên Nghĩa",
        "Tuyến xe buýt 31 Bách Khoa",
        "Tuyến xe buýt 01 Yên Nghĩa Gia Lâm",
        "Làm thế nào để đi từ Triều Khúc đến Đại học Bách Khoa?"
    ]
    
    for q in queries:
        print("=" * 60)
        print(f"QUERY: {q}")
        print("=" * 60)
        docs = db.similarity_search(q, k=3)
        print(format_docs(docs))
        print("\n")

if __name__ == "__main__":
    main()
