"""
ingest_all.py — Nạp toàn bộ file PDF/TXT/DOCX vào Pinecone Vector Store.
Sử dụng: venv\Scripts\python ingest_all.py
Yêu cầu: Đã cấu hình PINECONE_API_KEY và GEMINI_API_KEY trong .env
"""
import os
import sys

DATA_DIR         = "./data"
from config import settings
EMBED_MODEL      = settings.embedding_model
CHUNK_SIZE       = 1000
CHUNK_OVERLAP    = 200
SUPPORTED_EXT    = {".pdf", ".txt", ".docx"}

def main():
    print("=" * 55)
    print("  CompleteAI — Nạp dữ liệu lên Cloud Vector Store")
    print("=" * 55)

    if not os.path.exists(DATA_DIR):
        print(f"[LỖI] Không tìm thấy thư mục: {DATA_DIR}")
        sys.exit(1)

    files = []
    for root, _, fnames in os.walk(DATA_DIR):
        for fname in fnames:
            ext = os.path.splitext(fname.lower())[1]
            if ext in SUPPORTED_EXT:
                files.append(os.path.join(root, fname))

    if not files:
        print(f"[CẢNH BÁO] Không có file hợp lệ nào trong {DATA_DIR}")
        sys.exit(0)

    print(f"\nTìm thấy {len(files)} file(s):")
    for f in files:
        size_kb = os.path.getsize(f) / 1024
        print(f"  - {os.path.basename(f)} ({size_kb:.0f} KB)")

    print("\n[1/4] Đang khởi tạo mô hình Embedding...")
    if settings.embedding_engine == "gemini" and settings.gemini_api_key:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model, 
            google_api_key=settings.gemini_api_key
        )
        print("    [+] Sử dụng Google Gemini Embeddings.")
    else:
        print("    [!] Khuyên dùng Gemini Embeddings cho hệ thống Serverless.")
        from langchain_huggingface import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"}
        )

    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    if settings.pinecone_api_key:
        print("    [+] Kết nối Pinecone Vector Store...")
        from langchain_pinecone import PineconeVectorStore
        vectordb = PineconeVectorStore(
            index_name=settings.pinecone_index_name,
            embedding=embeddings,
            pinecone_api_key=settings.pinecone_api_key
        )
    elif settings.supabase_url and settings.supabase_key:
        print("    [+] Kết nối Supabase Vector Store...")
        from supabase.client import create_client
        from langchain_community.vectorstores import SupabaseVectorStore
        supabase_client = create_client(settings.supabase_url, settings.supabase_key)
        vectordb = SupabaseVectorStore(
            embedding=embeddings,
            client=supabase_client,
            table_name="documents",
            query_name="match_documents"
        )
    else:
        print("    [LỖI] Bạn cần khai báo pinecone_api_key trong .env để chạy!")
        sys.exit(1)

    total_chunks = 0
    for i, fpath in enumerate(files, 1):
        fname = os.path.basename(fpath)
        ext   = os.path.splitext(fname.lower())[1]
        print(f"\n[{i+1}/{len(files)+1}] Đang xử lý: {fname}")

        try:
            if ext == ".pdf":
                from langchain_community.document_loaders import PyPDFLoader
                docs = PyPDFLoader(fpath).load()
            elif ext == ".txt":
                from langchain_community.document_loaders import TextLoader
                docs = TextLoader(fpath, encoding="utf-8").load()
            elif ext == ".docx":
                from langchain_community.document_loaders import Docx2txtLoader
                docs = Docx2txtLoader(fpath).load()
            else:
                continue

            chunks = splitter.split_documents(docs)
            vectordb.add_documents(chunks)
            total_chunks += len(chunks)
            print(f"    OK: {len(docs)} trang -> {len(chunks)} đoạn văn bản")

        except Exception as e:
            print(f"    [LỖI] {fname}: {e}")

    print("\n" + "=" * 55)
    print(f"  HOÀN TẤT! Đã nạp {len(files)} file, tổng {total_chunks} đoạn.")
    print("  Dữ liệu đã được lưu trữ an toàn trên Đám Mây.")
    print("=" * 55)

if __name__ == "__main__":
    main()
