@echo on
cd /d %~dp0
echo Current directory: %CD%
"D:\IBKR_API\.venv\Scripts\python.exe" core/main.py
pause 