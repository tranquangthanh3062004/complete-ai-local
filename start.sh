#!/bin/bash

# Môi trường cho Streamlit biết Backend nằm ở đâu (localhost)
export BACKEND_URL="http://127.0.0.1:8000"

echo "Khởi động Backend (FastAPI)..."
uvicorn main:app --host 127.0.0.1 --port 8000 &

# Đợi vài giây cho backend khởi động
sleep 3

echo "Khởi động Frontend (Streamlit)..."
streamlit run app.py --server.port ${PORT:-8501} --server.address 0.0.0.0
