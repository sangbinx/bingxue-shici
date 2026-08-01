@echo off
chcp 65001 >nul
echo ========================================
echo   冰雪诗词 · 本地测试服务器
echo ========================================
echo.
echo 正在启动 HTTP 服务器...
echo.
start msedge http://localhost:8000/index.html
python -m http.server 8000
pause