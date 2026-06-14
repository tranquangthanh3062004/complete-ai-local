@echo off
chcp 65001 >nul
title GTCC Bot v4.0 - Chatbot Giao Thong Cong Cong

echo.
echo ==========================================================
echo      GTCC Bot v4.0 - Chatbot Giao Thong Cong Cong       
echo      Xe Buyt - Metro - BRT - Luat Giao Thong            
echo ==========================================================
echo.

REM -- Tim Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay Python!
    echo - Tai Python tai: https://python.org/downloads
    pause
    exit /b 1
)

REM -- Tao/kich hoat venv
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

REM -- Cai dependencies
echo.
echo [2/7] Kiem tra va cai dat thu vien...
pip install -r requirements.txt -q --no-warn-script-location
if %errorlevel% neq 0 (
    echo [LOI] Cai dat thu vien that bai!
    pause
    exit /b 1
)
echo    Thu vien san sang

REM -- Tao thu muc
echo.
echo [3/7] Tao thu muc can thiet...
if not exist data mkdir data
if not exist data\uploads mkdir data\uploads
if not exist chroma_db mkdir chroma_db
if not exist uploads mkdir uploads
echo    Thu muc san sang

REM -- Kiem tra Ollama
echo.
echo [4/7] Kiem tra Ollama...
netstat -ano | findstr ":11434 " >nul
if %errorlevel% equ 0 goto OLLAMA_RUNNING

echo    Ollama chua chay - dang khoi dong...
set "OLLAMA_EXE=ollama"
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
    set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
)
start /min "" "%OLLAMA_EXE%" serve
echo    Dang doi Ollama khoi tao (10 giay)...
timeout /t 10 /nobreak >nul

netstat -ano | findstr ":11434 " >nul
if %errorlevel% neq 0 (
    echo.
    echo    [CANH BAO] Khong khoi dong duoc Ollama!
    echo    Bot van chay nhung se dung fallback GTCC.
    echo    De co AI day du: chay "ollama serve" va thu lai.
    echo.
) else (
    echo    Ollama da khoi dong thanh cong
)
goto OLLAMA_DONE

:OLLAMA_RUNNING
echo    Ollama dang chay

:OLLAMA_DONE

REM -- Kiem tra model
echo.
echo [5/7] Danh sach model co san:
ollama list 2>nul || echo    (Ollama chua phan hoi - bot se dung fallback)

REM -- NAP DU LIEU GTCC
echo.
echo [6/7] Kiem tra va nap du lieu GTCC vao ChromaDB...

REM Kiem tra neu chroma_db co du lieu
set CHROMA_HAS_DATA=0
for /f %%i in ('dir /b /s chroma_db\*.bin 2^>nul ^| find /c /v ""') do set COUNT=%%i
if not "%COUNT%"=="0" (
    echo    ChromaDB da co du lieu - kiem tra cap nhat...
    set CHROMA_HAS_DATA=1
) else (
    echo    ChromaDB chua co du lieu - tien hanh nap...
)

if "%CHROMA_HAS_DATA%"=="0" (
    if exist data\gtcc_kienthuc.txt (
        echo    Dang nap gtcc_kienthuc.txt vao ChromaDB...
        python ingest_all.py
        echo    Nap du lieu GTCC hoan tat!
    ) else (
        echo    Khong co file data - bot se dung kien thuc co ban
    )
) else (
    echo    Bo qua buoc nap - du lieu da co san
)

:SKIP_INGEST

REM -- Don dep cac tien trinh cu
echo.
echo [7/7] Khoi dong Backend va Frontend...
echo.
echo    Don dep cac tien trinh cu...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8501 "') do taskkill /f /pid %%a >nul 2>&1

echo    Backend  - http://localhost:8000
echo    Frontend - http://localhost:8501
echo    API Docs - http://localhost:8000/docs
echo.

start "GTCC Bot Backend" cmd /k "title GTCC Bot Backend && call venv\Scripts\activate.bat && uvicorn main:app --reload --port 8000 --host 0.0.0.0 --log-level info"
timeout /t 6 /nobreak >nul

start "GTCC Bot Frontend" cmd /k "title GTCC Bot Frontend && call venv\Scripts\activate.bat && streamlit run app.py --server.port 8501 --server.headless false --browser.gatherUsageStats false"
timeout /t 4 /nobreak >nul

start http://localhost:8501

echo.
echo ==========================================================
echo    GTCC Bot v4.0 da khoi dong thanh cong!              
echo.
echo    Trinh duyet: http://localhost:8501               
echo    Backend API: http://localhost:8000/docs          
echo    Dang nhap:   admin@local.com / admin123          
echo.
echo    Tab "Hoi AI Truc Tiep" - chat ve GTCC            
echo    Tab "Hoi ve Tai Lieu" - hoi tu file da upload    
echo    Tab "Cau Hoi Thuong Gap" - FAQ ve GTCC           
echo    Tab "Quan Ly Tai Lieu" - upload file GTCC moi    
echo.
echo    Luu y: Bot van hoat dong khi Ollama offline      
echo    (se dung fallback co ban ve GTCC)                
echo.
echo    De tat: Dong 2 cua so CMD (Backend + Frontend)   
echo ==========================================================
echo.
pause
