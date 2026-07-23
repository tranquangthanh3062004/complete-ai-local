"""
Test GTCC-specific RAG search for origin and destination.
"""
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from services.ai_rag import get_vector_store, format_docs

def main():
    db = get_vector_store()
    
    orig = "Triều Khúc"
    dest = "Bách Khoa"
    
    q1 = f"Tuyến xe buýt {dest}"
    q2 = f"Tuyến xe buýt Nguyễn Trãi Yên Nghĩa"
    q3 = f"Lộ trình xe buýt Hà Nội qua {dest}"
    
    docs1 = db.similarity_search(q1, k=3)
    docs2 = db.similarity_search(q2, k=3)
    docs3 = db.similarity_search(q3, k=3)
    
    # Filter bus data files only
    all_docs = docs1 + docs2 + docs3
    bus_docs = [d for d in all_docs if any(k in d.metadata.get("source", "").lower() for k in ["buyt", "bus", "metro", "lich_trinh", "tuyen"])]
    
    print("=" * 60)
    print("MATCHED BUS DATA DOCUMENTS FROM RAG DATA FOLDER:")
    print("=" * 60)
    print(format_docs(bus_docs[:5]))

if __name__ == "__main__":
    main()
