# 🤖 CompleteAI v3.0 — Hướng Dẫn Sử Dụng

> **Hệ thống AI hoàn toàn cục bộ** — Không cần internet, không hết API, bảo mật tuyệt đối.

---

## ⚡ Khởi Động Nhanh (1 bước)

```
Nhấp đúp vào: START.bat
```

Hệ thống sẽ tự động:
1. Tạo môi trường Python ảo
2. Cài đặt tất cả thư viện
3. Khởi động Ollama (nếu chưa chạy)
4. Mở Backend + Frontend
5. Tự mở trình duyệt tại `http://localhost:8501`

---

## 📋 Yêu Cầu Hệ Thống

| Thành phần | Yêu cầu |
|------------|---------|
| **Python** | 3.10+ — [python.org](https://python.org) |
| **Ollama** | Cài tại [ollama.com](https://ollama.com) |
| **RAM**    | Tối thiểu 8GB (khuyến nghị 16GB) |
| **Disk**   | 5–10GB cho model AI |

---

## 🧠 Cài Model AI (chỉ làm 1 lần)

Mở terminal và chạy **một trong các lệnh** sau:

```bash
# Khuyến nghị — Tiếng Việt rất tốt, nhẹ
ollama pull qwen2.5:7b

# Hoặc — Model phổ thông
ollama pull llama3.2

# Hoặc — Siêu nhẹ (máy yếu)
ollama pull phi3:mini

# Kiểm tra model đã cài
ollama list
```

---

## 🔧 Đổi Model Mặc Định

Sửa file `.env` (tạo nếu chưa có):

```env
OLLAMA_MODEL=qwen2.5:7b
```

Hoặc đổi trực tiếp trong UI — Sidebar → **"Tải danh sách model"** → chọn model.

---

## 🌐 Các Địa Chỉ Quan Trọng

| Dịch vụ | Địa chỉ |
|---------|---------|
| 🖥️ Giao diện chat | http://localhost:8501 |
| 📡 Backend API | http://localhost:8000 |
| 📖 API Docs (Swagger) | http://localhost:8000/docs |
| 🔬 Ollama | http://localhost:11434 |

---

## 👤 Tài Khoản Mặc Định

```
Email:    admin@local.com
Mật khẩu: admin123
```

> Có thể dùng chế độ **Khách** mà không cần đăng nhập.

---

## 🚀 Tính Năng Hệ Thống

### 💬 Chat Trực Tiếp
- Chat với AI qua Ollama local
- **Nhớ ngữ cảnh hội thoại** (conversation memory)
- **Chọn model** trực tiếp trên UI (Sidebar)
- **Điều chỉnh Temperature** (độ sáng tạo)
- 👍/👎 feedback để cải thiện AI
- **Gợi ý câu hỏi tiếp theo** tự động
- **Xuất lịch sử chat** ra file `.txt`

### 📚 RAG — Hỏi Tài Liệu
- Upload **PDF, DOCX, TXT**
- AI tìm kiếm trong tài liệu và trả lời có nguồn
- **Hiển thị đoạn trích** từ tài liệu gốc
- Xóa tài liệu không cần nữa

### 📊 Phân Tích Học Tập
- Radar chart điểm mạnh/yếu theo chủ đề
- Bar chart số câu hỏi đã hỏi
- Lịch sử 5 câu hỏi gần nhất

---

## 🛠️ Xử Lý Sự Cố

### ❌ Không kết nối được backend
```bash
# Kích hoạt venv rồi chạy:
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

### ❌ Ollama offline
```bash
ollama serve
```

### ❌ Lỗi thư viện thiếu
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### ❌ Lỗi cài docx2txt (cho file .docx)
```bash
pip install docx2txt
```

### ❌ Model chưa được pull
```bash
ollama pull qwen2.5:7b   # hoặc tên model bạn muốn
```

---

## 📁 Cấu Trúc Thư Mục

```
my_open_llm/
├── START.bat          ← Khởi động (dùng cái này!)
├── app.py             ← Giao diện Streamlit
├── main.py            ← FastAPI Backend
├── config.py          ← Cấu hình hệ thống
├── llm_factory.py     ← Kết nối Ollama (cached)
├── database.py        ← SQLite Database
├── models.py          ← Database models
├── routers/
│   ├── agents.py      ← Chat API (memory + suggestions)
│   ├── rag.py         ← RAG API (PDF/DOCX/TXT)
│   ├── learning.py    ← Feedback + Analytics API
│   └── auth.py        ← Xác thực JWT
├── data/uploads/      ← File tải lên (tạm thời)
├── chroma_db/         ← Vector database (tài liệu)
├── completeai.db      ← SQLite database
├── requirements.txt   ← Danh sách thư viện
└── .env               ← Cấu hình riêng (tạo thủ công)
```

---

## ⚙️ Cấu Hình Nâng Cao (file `.env`)

```env
# Model AI chính
OLLAMA_MODEL=qwen2.5:7b

# Địa chỉ Ollama (mặc định localhost)
OLLAMA_BASE_URL=http://localhost:11434

# Giới hạn file upload (MB)
MAX_UPLOAD_MB=50

# Kích thước đoạn văn bản khi index
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Số tài liệu lấy khi RAG search
RAG_TOP_K=4
```

---

## 🔄 Cập Nhật Hệ Thống

```bash
# Kích hoạt venv
venv\Scripts\activate

# Cập nhật thư viện
pip install -r requirements.txt --upgrade
```

---

*CompleteAI v3.0 — Build ngày 2026-04-19*
