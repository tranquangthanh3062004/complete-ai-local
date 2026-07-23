@echo off
chcp 65001 >nul
title COMPLETE AI Assistant - Startup Script

echo ==========================================================
echo      COMPLETE AI Assistant - Khởi động Hệ thống (Local)       
echo ==========================================================
echo.

REM -- Dọn dẹp tiến trình cũ
echo [1/4] Dọn dẹp các cổng đang sử dụng (8000, 5173)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173 "') do taskkill /f /pid %%a >nul 2>&1

echo.
echo [2/4] Khởi động Backend (FastAPI)...
if exist venv (
    start "COMPLETE AI Backend" cmd /k "title COMPLETE AI Backend && call venv\Scripts\activate.bat && pip install -r requirements.txt -q && uvicorn main:app --reload --port 8000 --host 0.0.0.0"
) else (
    start "COMPLETE AI Backend" cmd /k "title COMPLETE AI Backend && uvicorn main:app --reload --port 8000 --host 0.0.0.0"
)

echo    Đang chờ Backend khởi động (5 giây)...
timeout /t 5 /nobreak >nul

echo.
echo [3/4] Khởi động Frontend (React / Vite)...
start "COMPLETE AI Frontend" cmd /k "title COMPLETE AI Frontend && cd frontend && npm install && npm run dev"

echo    Đang chờ Frontend khởi động (5 giây)...
timeout /t 5 /nobreak >nul

echo.
echo [4/4] Mở trình duyệt...
start http://localhost:5173

echo.
echo ==========================================================
echo    Hệ thống đã khởi động thành công!              
echo.
echo    Giao diện Web: http://localhost:5173               
echo    Backend API:   http://localhost:8000/docs          
echo.
echo    Để tắt hệ thống: Đóng 2 cửa sổ CMD vừa bật.
echo ==========================================================
echo.
pause
