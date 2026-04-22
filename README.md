# 🤖 CompleteAI v3.0 — Hệ Thống Trợ Lý AI Hoàn Toàn Cục Bộ

> **Bảo mật tuyệt đối** — Không cần internet, không giới hạn API, dữ liệu không bao giờ rời khỏi máy của bạn.

CompleteAI v3.0 là một dự án kết hợp sức mạnh của **FastAPI** (Backend), **Streamlit** (Frontend) và **Ollama** (Local LLM) để tạo ra một hệ thống AI mạnh mẽ chạy ngay trên máy tính cá nhân. Hệ thống tích hợp RAG để đọc và trả lời dựa trên tài liệu (PDF, DOCX, TXT) cùng tính năng theo dõi học tập (Analytics).

---

## ✨ Tính Năng Nổi Bật

- **💬 Chat Thông Minh (Memory):** Ghi nhớ ngữ cảnh trò chuyện như ChatGPT.
- **📚 RAG Đa Định Dạng:** Upload PDF, DOCX, TXT. Trích xuất chính xác văn bản nguồn khi trả lời.
- **⚙️ Tùy Chỉnh LLM:** Chuyển đổi Model (Llama3, Qwen, Phi3...) và độ sáng tạo (Temperature) ngay trên UI.
- **📊 Analytics Profile:** Vẽ biểu đồ Radar và Bar Chart đánh giá điểm mạnh/yếu của người dùng.
- **⚡ Tự Động Hóa:** Chỉ cần chạy `START.bat` để tự động thiết lập mọi thứ (venv, libs, server, ingest data).

---

## ⚡ Khởi Động Nhanh (Windows)

1. Clone repository này về máy.
2. Cài đặt Python 3.10+ (Tick "Add Python to PATH") và cài đặt [Ollama](https://ollama.com).
3. Mở thư mục dự án và nhấp đúp vào file `START.bat`.

Hệ thống sẽ tự động cài đặt thư viện, bật Ollama, và mở giao diện tại `http://localhost:8501`.

---

## 📋 Yêu Cầu Hệ Thống

| Thành phần | Yêu cầu |
|------------|---------|
| **Python** | 3.10+ |
| **Ollama** | Đã cài đặt và đang chạy |
| **RAM**    | Tối thiểu 8GB (khuyến nghị 16GB) |

### 🧠 Tải Model AI

Mở terminal và chạy lệnh để tải model (Ví dụ: Qwen 2.5 cực tốt cho Tiếng Việt):
```bash
ollama pull qwen2.5:7b
# Hoặc model siêu nhẹ cho máy yếu:
ollama pull phi3:mini
```

---

## 📁 Cấu Trúc Dự Án

```
my_open_llm/
├── START.bat          ← Script khởi động tự động
├── app.py             ← Giao diện Streamlit
├── main.py            ← FastAPI Backend
├── config.py          ← Cấu hình hệ thống
├── llm_factory.py     ← Quản lý kết nối Ollama
├── ingest_all.py      ← Script tự nạp tài liệu vào ChromaDB
├── routers/
│   ├── agents.py      ← API Chat & Memory
│   ├── rag.py         ← API RAG (Xử lý file)
│   ├── learning.py    ← API Feedback & Analytics
│   └── auth.py        ← API Xác thực
├── requirements.txt   ← Các thư viện cần thiết
└── .gitignore         ← Bỏ qua venv và db khi push
```

---

## ⚙️ Cấu Hình (.env)
Bạn có thể tạo file `.env` ở thư mục gốc để thay đổi cấu hình mặc định:
```env
OLLAMA_MODEL=qwen2.5:7b
MAX_UPLOAD_MB=50
CHUNK_SIZE=1000
```

---

*Dự án mã nguồn mở phục vụ mục đích học tập và làm việc cá nhân.*
