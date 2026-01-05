@echo off
cd /d C:\Users\BVH\koine_phrase_app

REM Start the Streamlit server in its own window (keeps running)
start "Koine App Server" /min python -m streamlit run app.py --server.port 8501

REM Give it a second to start, then open browser
timeout /t 2 >nul
start "" http://localhost:8501

exit
