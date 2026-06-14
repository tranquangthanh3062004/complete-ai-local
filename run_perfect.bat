@echo off
echo === CompleteAI - Run Perfect (Fixed All Errors) ===
echo 1. Install deps...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo 2. Start Ollama (need download llama3 1st time)...
netstat -ano | findstr ":11434 " >nul
if %errorlevel% neq 0 (
    start cmd /k "ollama serve"
    timeout /t 5
) else (
    echo Ollama already running!
)
ollama pull llama3
timeout /t 10

echo 3. Ingest PDF → chroma_db...
python ingest.py

echo 4. Cleanup old processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8501 "') do taskkill /f /pid %%a >nul 2>&1

echo 5. Backend API...
start cmd /k "uvicorn main:app --reload --port 8000"

echo 6. Frontend UI...
start cmd /k "streamlit run app.py"

echo === ALL RUNNING! ===
echo - Backend: http://localhost:8000/health (check seed DB)
echo - UI: http://localhost:8501 (login admin/admin123 if need)
echo - Test RAG: "luật giao thông là gì?"
echo Press any key to exit...
pause >nul

