@echo off
echo Dang chay qua trinh day len GitHub, vui long cho may giay...
(
echo ==========================================
echo DANG DAY DU LIEU LEN GITHUB...
echo ==========================================
echo.
echo [1] Khoi tao Git...
git init
echo.
echo [2] Them file vao Git...
git add .
echo.
echo [3] Tao commit...
git commit -m "Initial commit"
echo.
echo [4] Chuyen nhanh main...
git branch -M main
echo.
echo [5] Ket noi URL...
git remote set-url origin https://github.com/tranquangthanh3062004/complete-ai-local.git 2>nul
if errorlevel 1 git remote add origin https://github.com/tranquangthanh3062004/complete-ai-local.git
echo.
echo [6] Day ma nguon len Github...
git push -u origin main
) > git_log.txt 2>&1

echo.
echo ========================================================
echo DA CHAY XONG! DA LUU KET QUA VAO FILE "git_log.txt".
echo ========================================================
pause
