#!/bin/bash

echo "Khởi động Backend (FastAPI) phục vụ cả API và React SPA..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
