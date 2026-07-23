"""
ingest_local.py — Script nạp dữ liệu Local vào ChromaDB dùng HuggingFace Embeddings (100% Fast, Offline, No Rate Limit).
"""
import os
import shutil
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from config import settings

DATA_DIR = "./data"
CHROMA_DIR = settings.chroma_persist_dir or "./chroma_db"
COLLECTION_NAME = "gtcc_docs"

print("=" * 60)
print("  COMPLETE AI - Re-indexing Local Vector Database (ChromaDB)")
print("=" * 60)

# 1. Clear old ChromaDB
if os.path.exists(CHROMA_DIR):
    print(f"[1/4] Xoa du lieu cu tai: {CHROMA_DIR}...")
    try:
        shutil.rmtree(CHROMA_DIR)
        print("    [OK] Da xoa thu muc ChromaDB cu.")
    except Exception as e:
        print(f"    [WARN] Khong the xoa: {e}")

# 2. Init Embeddings
print("[2/4] Khoi tao mo hinh Local Embedding (all-MiniLM-L6-v2)...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 3. Collect files
print(f"[3/4] Quet file trong: {DATA_DIR}...")
files = []
for root, _, fnames in os.walk(DATA_DIR):
    for fname in fnames:
        ext = os.path.splitext(fname.lower())[1]
        if ext in {".txt", ".pdf"}:
            files.append(os.path.join(root, fname))

print(f"    Tim thay {len(files)} file du lieu.")

splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
all_docs = []

for fpath in files:
    fname = os.path.basename(fpath)
    ext = os.path.splitext(fname.lower())[1]
    try:
        if ext == ".txt":
            docs = TextLoader(fpath, encoding="utf-8").load()
        elif ext == ".pdf":
            docs = PyPDFLoader(fpath).load()
        else:
            continue
            
        chunks = splitter.split_documents(docs)
        for chunk in chunks:
            chunk.metadata["source"] = fname
        all_docs.extend(chunks)
        print(f"    - {fname}: {len(chunks)} doan")
    except Exception as e:
        print(f"    [LOI] {fname}: {e}")

print(f"\nTong doan van ban: {len(all_docs)}")

# 4. Save to ChromaDB
print(f"[4/4] Luu vao ChromaDB local ({CHROMA_DIR}, collection='{COLLECTION_NAME}')...")
os.makedirs(CHROMA_DIR, exist_ok=True)

vectordb = Chroma.from_documents(
    documents=all_docs,
    embedding=embeddings,
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_DIR
)

print("\n" + "=" * 60)
print(f"  HOAN TAT! Da nap {len(all_docs)} doan vao ChromaDB Local thanh cong!")
print("=" * 60)
