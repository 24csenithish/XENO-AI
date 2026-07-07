# run.py
import subprocess
import sys
import os
import webbrowser
import time
import threading

def run_streamlit():
    os.system(f"\"{sys.executable}\" -m streamlit run frontend/app.py --server.port 8501 --server.headless true")

def run_fastapi():
    os.system(f"\"{sys.executable}\" -m uvicorn app.api.server:create_app --factory --host 127.0.0.1 --port 8000 --reload")

if __name__ == "__main__":
    print("XENO AI - Starting services...")
    # Start FastAPI in background
    threading.Thread(target=run_fastapi, daemon=True).start()
    time.sleep(2)  # Give API time to start
    # Open browser to Streamlit
    webbrowser.open("http://localhost:8501")
    # Run Streamlit in foreground
    run_streamlit()