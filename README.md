# GTCC Bot v4.0 — Chatbot Giao Thông Công Cộng Việt Nam

## Mô tả
Chatbot AI hỏi đáp về **Giao Thông Công Cộng (GTCC)** tại Việt Nam.  
Sử dụng Ollama (AI cục bộ) + RAG (tìm kiếm tài liệu) + fallback thông minh.

## Tính năng chính
- 🚌 Hỏi đáp về xe buýt (tuyến, giá vé, lịch trình)
- 🚇 Thông tin metro (Hà Nội, TP.HCM)
- 🚍 BRT - Xe buýt nhanh
- 🎫 Vé & ưu đãi (học sinh, người cao tuổi, người khuyết tật)
- 📋 Luật & quy định giao thông
- ⛵ Giao thông đường thủy (buýt sông)
- 📱 Ứng dụng tra cứu GTCC
- ❓ FAQ về GTCC (câu hỏi thường gặp)
- 📊 Thống kê hệ thống
- 📁 Upload tài liệu GTCC (PDF/TXT/DOCX)

## Khởi động
```bash
# Cách 1: Chạy file batch (Windows)
START.bat

# Cách 2: Thủ công
venv\Scripts\activate
uvicorn main:app --reload --port 8000
streamlit run app.py --server.port 8501
```

## Truy cập
- Frontend: http://localhost:8501
- API Docs: http://localhost:8000/docs
- Login: admin@local.com / admin123

## Cấu trúc thư mục
```
my_open_llm/
├── main.py              # FastAPI backend
├── app.py               # Streamlit frontend
├── config.py            # Cấu hình hệ thống
├── routers/
│   ├── agents.py        # Chat AI về GTCC
│   ├── rag.py           # RAG + topic detection GTCC
│   ├── auth.py          # Xác thực
│   └── learning.py      # Feedback & thống kê
├── data/
│   └── gtcc_kienthuc.txt  # Dữ liệu kiến thức GTCC
├── chroma_db/           # Vector database (tự động tạo)
├── START.bat            # Khởi động tất cả
└── NANG_CAP.md          # Gợi ý nâng cấp hệ thống
```

## Lưu ý
- Bot **vẫn hoạt động** khi Ollama offline (dùng fallback GTCC)
- ChromaDB lưu embedding — **không cần nạp lại** mỗi lần khởi động
- Upload thêm tài liệu GTCC để bot trả lời chính xác hơn
