"""
reset_and_reingest.py — Xoa ChromaDB cu va nap lai toan bo du lieu GTCC moi.
Chay: venv\Scripts\python reset_and_reingest.py
"""
import os, shutil

CHROMA_DIR = "./chroma_db"

print("=" * 50)
print("  RESET & RE-INGEST DU LIEU GTCC")
print("=" * 50)

# Xoa ChromaDB cu
if os.path.exists(CHROMA_DIR):
    shutil.rmtree(CHROMA_DIR)
    print(f"[OK] Da xoa ChromaDB cu: {CHROMA_DIR}")
else:
    print("[INFO] ChromaDB chua ton tai, bo qua.")

# Nap lai
print("\n[NAP] Bat dau nap du lieu moi...")
os.makedirs(CHROMA_DIR, exist_ok=True)

import sys
sys.path.insert(0, ".")

# Chay ingest_all
import ingest_all
ingest_all.main()

print("\n[HOAN TAT] Du lieu GTCC moi da duoc nap vao ChromaDB.")
print("  Ban co the chay START.bat de khoi dong bot.")
