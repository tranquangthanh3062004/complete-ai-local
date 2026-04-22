@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║         CompleteAI - Khởi Động Hệ Thống AI          ║
echo ║         Hoàn toàn cục bộ - Không cần internet       ║
echo ╚══════════════════════════════════════════════════════╝
echo.

REM ── Kích hoạt venv ──────────────────────────────────────────────────────────
if not exist venv (
    echo [1/5] Tạo môi trường Python ảo...
    python -m venv venv
) else (
    echo [1/5] Môi trường ảo đã tồn tại ✓
)
call venv\Scripts\activate.bat

REM ── Cài đặt dependencies ────────────────────────────────────────────────────
echo.
echo [2/5] Cài đặt/cập nhật thư viện...
pip install -r requirements.txt -q --upgrade
if %errorlevel% neq 0 (
    echo    LỖI: Cài đặt thất bại!
    pause
    exit /b 1
)
echo    Thư viện đã sẵn sàng ✓

REM ── Kiểm tra Ollama ─────────────────────────────────────────────────────────
echo.
echo [3/5] Kiểm tra Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo    ⚠️  Ollama chưa chạy!
    echo    → Đang thử khởi động Ollama...
    start /min "" ollama serve
    timeout /t 3 /nobreak >nul
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if %errorlevel% neq 0 (
        echo    ❌ Không thể khởi động Ollama tự động.
        echo    → Vui lòng mở terminal khác và chạy: ollama serve
        echo    → Sau đó chạy lại file này.
        pause
        exit /b 1
    )
)
echo    Ollama đang chạy ✓

REM ── Kiểm tra model ──────────────────────────────────────────────────────────
echo.
echo [4/5] Kiểm tra model AI...
for /f "tokens=*" %%i in ('curl -s http://localhost:11434/api/tags') do set TAGS=%%i
echo    Models có sẵn trong Ollama:
ollama list

REM Thử pull model mặc định nếu chưa có
REM ollama pull llama3.2

REM ── Khởi động Backend và Frontend song song ──────────────────────────────────
echo.
echo [5/5] Khởi động Backend và Frontend...
echo.
echo    Backend  → http://localhost:8000
echo    Frontend → http://localhost:8501
echo    API Docs → http://localhost:8000/docs
echo.

REM Khởi động backend trong cửa sổ mới
start "CompleteAI Backend" cmd /k "call venv\Scripts\activate.bat && uvicorn main:app --reload --port 8000 --host 0.0.0.0"

REM Đợi backend khởi động
timeout /t 4 /nobreak >nul

REM Khởi động frontend trong cửa sổ mới
start "CompleteAI Frontend" cmd /k "call venv\Scripts\activate.bat && streamlit run app.py --server.port 8501 --server.headless false"

REM Đợi frontend khởi động
timeout /t 3 /nobreak >nul

REM Mở trình duyệt
start http://localhost:8501

echo.
echo ══════════════════════════════════════════════════════
echo    ✅ Hệ thống đã khởi động!
echo    → Trình duyệt sẽ tự mở http://localhost:8501
echo    → Đăng nhập: admin@local.com / admin123
echo.
echo    Để tắt: đóng 2 cửa sổ "CompleteAI Backend/Frontend"
echo ══════════════════════════════════════════════════════
echo.
pause
