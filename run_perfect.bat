@echo off
echo === CompleteAI - Run Perfect (Fixed All Errors) ===
echo 1. Install deps...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo 2. Start Ollama (need download llama3 1st time)...
start cmd /k "ollama serve"
timeout /t 5
ollama pull llama3
timeout /t 10

echo 3. Ingest PDF → chroma_db...
python ingest.py

echo 4. Backend API...
start cmd /k "uvicorn main:app --reload --port 8000"

echo 5. Frontend UI...
start cmd /k "streamlit run app.py"

echo === ALL RUNNING! ===
echo - Backend: http://localhost:8000/health (check seed DB)
echo - UI: http://localhost:8501 (login admin/admin123 if need)
echo - Test RAG: "luật giao thông là gì?"
echo Press any key to exit...
pause >nul

