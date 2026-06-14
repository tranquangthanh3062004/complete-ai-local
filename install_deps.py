"""Script cai dat tat ca dependencies cho Python 3.13 tren Windows"""
import subprocess
import sys
import os

# Fix encoding cho Windows terminal
os.environ["PYTHONIOENCODING"] = "utf-8"

python = sys.executable

packages_core = [
    "fastapi",
    "uvicorn[standard]",
    "python-multipart",
    "python-dotenv",
    "sqlalchemy",
    "aiosqlite",
    "python-jose[cryptography]",
    "passlib[bcrypt]",
    "pydantic",
    "pydantic-settings",
    "httpx",
    "requests",
    "alembic",
]

dl    "langchain",
    "langchain-core",
    "langchain-community",
    "langchain-ollama",
    "langchain-huggingface",
    "langchain-text-splitters",
    "langchain-chroma",
]
    
packages_vector = [
    "chromadb",
]

packages_doc = [
    "pypdf",
    "numpy",
    "sentence-transformers",
]

packages_frontend = [
    "streamlit",
    "plotly",
]

packages_test = [
    "pytest",
    "pytest-asyncio",
]

all_groups = [
    ("Core Web", packages_core),
    ("LLM", packages_llm),
    ("Vector DB", packages_vector),
    ("Documents", packages_doc),
    ("Frontend", packages_frontend),
    ("Testing", packages_test),
]

def install(pkgs, label):
    print("")
    print("=" * 50)
    print("Installing: " + label)
    print("=" * 50)
    cmd = [python, "-m", "pip", "install"] + pkgs + ["--upgrade", "-q"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        stderr = result.stderr[-2000:] if result.stderr else ""
        stdout = result.stdout[-500:] if result.stdout else ""
        print("STDERR: " + stderr)
        print("STDOUT: " + stdout)
        return False
    print("OK: " + label + " installed successfully")
    return True

failed = []
for label, pkgs in all_groups:
    ok = install(pkgs, label)
    if not ok:
        failed.append(label)

print("")
print("=" * 50)
if failed:
    print("FAILED groups: " + str(failed))
    print("Trying to install failed packages individually...")
    for label in failed:
        for group_label, pkgs in all_groups:
            if group_label == label:
                for pkg in pkgs:
                    r = subprocess.run(
                        [python, "-m", "pip", "install", pkg, "-q"],
                        capture_output=True, text=True, encoding="utf-8", errors="replace"
                    )
                    status = "OK" if r.returncode == 0 else "FAILED"
                    print(f"  {status}: {pkg}")
else:
    print("ALL DONE: Dependencies installed successfully!")
