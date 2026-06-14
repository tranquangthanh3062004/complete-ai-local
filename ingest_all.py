"""
ingest_all.py — Nạp toàn bộ file PDF/TXT từ thư mục data/ vào ChromaDB.
Chạy một lần: venv\Scripts\python ingest_all.py
"""
import os
import sys

# ── Thư mục chứa file cần nạp ─────────────────────────────────────────────────
DATA_DIR         = "./data"
CHROMA_DIR       = "./chroma_db"
EMBED_MODEL      = "keepitreal/vietnamese-sbert"
CHUNK_SIZE       = 1000
CHUNK_OVERLAP    = 200

SUPPORTED_EXT    = {".pdf", ".txt", ".docx"}

def main():
    print("=" * 55)
    print("  CompleteAI — Nap du lieu vao ChromaDB")
    print("=" * 55)

    # Kiểm tra thư mục
    if not os.path.exists(DATA_DIR):
        print(f"[LOI] Khong tim thay thu muc: {DATA_DIR}")
        sys.exit(1)

    # Tìm tất cả file hỗ trợ
    files = []
    for root, _, fnames in os.walk(DATA_DIR):
        for fname in fnames:
            ext = os.path.splitext(fname.lower())[1]
            if ext in SUPPORTED_EXT:
                files.append(os.path.join(root, fname))

    if not files:
        print(f"[CANH BAO] Khong co file PDF/TXT/DOCX nao trong {DATA_DIR}")
        sys.exit(0)

    print(f"\nTim thay {len(files)} file(s):")
    for f in files:
        size_kb = os.path.getsize(f) / 1024
        print(f"  - {os.path.basename(f)} ({size_kb:.0f} KB)")

    # ── Import libraries ──────────────────────────────────────────────────────
    print("\n[1/4] Dang khoi tao mo hinh Embedding...")
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_chroma import Chroma

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    print("    Mo hinh Embedding san sang.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    from config import settings
    if settings.supabase_url and settings.supabase_key:
        print("    [+] Ket noi Supabase Vector Store...")
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
        print("    [+] Khoi tao ChromaDB (Local)...")
        from langchain_chroma import Chroma
        os.makedirs(CHROMA_DIR, exist_ok=True)
        vectordb = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings,
        )

    # ── Nạp từng file ─────────────────────────────────────────────────────────
    total_chunks = 0
    for i, fpath in enumerate(files, 1):
        fname = os.path.basename(fpath)
        ext   = os.path.splitext(fname.lower())[1]
        print(f"\n[{i+1}/4] Dang xu ly: {fname}")

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
            print(f"    OK: {len(docs)} trang -> {len(chunks)} doan van ban")

        except Exception as e:
            print(f"    [LOI] {fname}: {e}")

    print("\n" + "=" * 55)
    print(f"  HOAN TAT! Da nap {len(files)} file, tong {total_chunks} doan.")
    print(f"  Du lieu luu tai: {CHROMA_DIR}")
    print("  Gio ban co the hoi AI ve noi dung cac tai lieu nay.")
    print("=" * 55)


if __name__ == "__main__":
    main()
