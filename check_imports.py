"""Kiem tra tat ca import truoc khi chay backend."""
import sys
sys.path.insert(0, ".")

errors = []

tests = [
    ("config",           "from config import settings"),
    ("models",           "from models import User, Document, Chat, LearningEvent, TopicMastery"),
    ("database",         "from database import get_db, create_tables, seed_superuser"),
    ("llm_factory",      "from llm_factory import get_llm, get_available_models"),
    ("routers.auth",     "from routers.auth import router, get_current_user"),
    ("routers.rag",      "from routers.rag import router"),
    ("routers.agents",   "from routers.agents import router"),
    ("routers.learning", "from routers.learning import router"),
    ("main",             "from main import app"),
]

for name, stmt in tests:
    try:
        exec(stmt)
        print("OK: " + name)
    except Exception as e:
        print("FAIL: " + name + " => " + str(e))
        errors.append((name, str(e)))

print("")
if errors:
    print("ERRORS FOUND: " + str(len(errors)))
    for n, e in errors:
        print("  - " + n + ": " + e)
    sys.exit(1)
else:
    print("ALL IMPORTS OK - Ready to start!")
