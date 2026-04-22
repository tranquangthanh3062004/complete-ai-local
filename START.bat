@echo off
chcp 65001 >nul
title CompleteAI v3.0 - Launcher

echo.
echo ==========================================================
echo           CompleteAI v3.0 - Khoi Dong He Thong AI        
echo      Hoan toan cuc bo - Khong can internet - Bao mat     
echo ==========================================================
echo.

REM -- Tim Python ---------------------------------------------------------------
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay Python!
    echo - Tai Python tai: https://python.org/downloads
    echo - Nho tick "Add Python to PATH" khi cai dat!
    pause
    exit /b 1
)

REM -- Tao/kich hoat venv -------------------------------------------------------
if not exist venv (
    echo [1/7] Tao moi truong Python ao...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [LOI] Khong tao duoc venv!
        pause
        exit /b 1
    )
) else (
    echo [1/7] Moi truong ao da ton tai
)
call venv\Scripts\activate.bat

REM -- Cai dependencies ---------------------------------------------------------
echo.
echo [2/7] Kiem tra va cai dat thu vien...
pip install -r requirements.txt -q --no-warn-script-location
if %errorlevel% neq 0 (
    echo [LOI] Cai dat thu vien that bai!
    echo - Thu chay tay: pip install -r requirements.txt
    pause
    exit /b 1
)
echo    Thu vien san sang

REM -- Tao thu muc can thiet ----------------------------------------------------
echo.
echo [3/7] Tao thu muc can thiet...
if not exist data mkdir data
if not exist data\uploads mkdir data\uploads
if not exist chroma_db mkdir chroma_db
if not exist uploads mkdir uploads
echo    Thu muc san sang

REM -- Kiem tra Ollama ----------------------------------------------------------
echo.
echo [4/7] Kiem tra Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo    Ollama chua chay - dang khoi dong...
    start /min "" ollama serve
    timeout /t 5 /nobreak >nul
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo    =============================================
        echo      CANH BAO: Khong tu khoi dong duoc Ollama!        
        echo      - Mo terminal khac va chay: ollama serve   
        echo      - Sau do bam phim bat ky de tiep tuc      
        echo    =============================================
        pause >nul
    ) else (
        echo    Ollama da khoi dong
    )
) else (
    echo    Ollama dang chay
)

REM -- Kiem tra model -----------------------------------------------------------
echo.
echo [5/7] Danh sach model co san:
ollama list 2>nul || echo    (Ollama chua phan hoi)

REM -- Nap du lieu PDF tu thu muc data/ ----------------------------------------
echo.
echo [6/7] Nap du lieu PDF tu thu muc data/...
if exist data\*.pdf (
    echo    Tim thay file PDF - dang nap vao ChromaDB...
    python ingest_all.py
    echo    Nap du lieu hoan tat!
) else if exist data\*.txt (
    echo    Tim thay file TXT - dang nap vao ChromaDB...
    python ingest_all.py
    echo    Nap du lieu hoan tat!
) else (
    echo    Khong co file moi trong data/ - bo qua buoc nay
)

REM -- Khoi dong Backend + Frontend ---------------------------------------------
echo.
echo [7/7] Khoi dong Backend va Frontend...
echo.
echo    Backend  - http://localhost:8000
echo    Frontend - http://localhost:8501
echo    API Docs - http://localhost:8000/docs
echo.

start "CompleteAI Backend" cmd /k "title CompleteAI Backend && call venv\Scripts\activate.bat && uvicorn main:app --reload --port 8000 --host 0.0.0.0 --log-level info"
timeout /t 6 /nobreak >nul

start "CompleteAI Frontend" cmd /k "title CompleteAI Frontend && call venv\Scripts\activate.bat && streamlit run app.py --server.port 8501 --server.headless false --browser.gatherUsageStats false"
timeout /t 4 /nobreak >nul

start http://localhost:8501

echo.
echo ==========================================================
echo    CompleteAI v3.0 da khoi dong thanh cong!            
echo.
echo    Trinh duyet: http://localhost:8501                  
echo    Backend API: http://localhost:8000/docs             
echo    Dang nhap:   admin@local.com / admin123             
echo.
echo    Tab "RAG - Hoi Tai Lieu" de chat ve file PDF da nap
echo    Tab "Quan Ly Tai Lieu" de upload file moi           
echo.
echo    De tat: Dong 2 cua so CMD (Backend + Frontend)         
echo ==========================================================
echo.
pause
