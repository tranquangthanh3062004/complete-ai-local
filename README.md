# 🚌 GTCC Bot v5.1 — Nền tảng AI Trợ lý Giao Thông Công Cộng Việt Nam

![Version](https://img.shields.io/badge/version-5.1.0-blue)
![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18.x-blue?logo=react&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker&logoColor=white)

**GTCC Bot** là một Hệ thống Trí tuệ Nhân tạo toàn diện hỗ trợ hỏi đáp, tư vấn, và tra cứu thông tin Giao Thông Công Cộng tại Việt Nam. Sản phẩm được thiết kế theo tiêu chuẩn Production, tích hợp RAG (Retrieval-Augmented Generation), Tìm đường thông minh, và Dashboard phân tích dữ liệu.

---

## ✨ Tính năng Nổi bật (Core Features)

1. 🤖 **AI Chatbot (RAG System)**: 
   - Giải đáp thông tin tuyến Xe buýt, Metro (Bến Thành - Suối Tiên, Cát Linh - Hà Đông), BRT, Giá vé, Luật giao thông.
   - Hỗ trợ công nghệ đọc văn bản thành giọng nói (TTS - Text-to-Speech).
   - Tự động gợi ý các câu hỏi liên quan và nhận diện ý định người dùng.

2. 🗺️ **Bản đồ & Tìm đường Thông minh (Smart Routing)**:
   - Thuật toán định tuyến Dijkstra để tìm lộ trình tối ưu qua các trạm xe buýt/metro.
   - Trực quan hóa tuyến đường trên bản đồ thực tế với `react-leaflet` và OpenStreetMap.
   - Ước tính thời gian, chi phí, và số lần chuyển tuyến.

3. 📊 **Admin Dashboard & Analytics**:
   - Giao diện quản trị viên thống kê tốc độ phát triển và chất lượng hệ thống.
   - Biểu đồ thời gian thực sử dụng `recharts`: Số lượt câu hỏi, Tỉ lệ người dùng hài lòng (👍/👎), Top chủ đề được quan tâm, Tốc độ phản hồi trung bình.

4. 🔐 **Hệ thống Định danh & Cá nhân hóa**:
   - Đăng nhập bảo mật đa kênh (Local JWT Auth, Google OAuth2).
   - Lưu trữ lịch sử tìm kiếm, lịch sử chat và theo dõi tiến độ hiểu biết (Topic Mastery) của từng cá nhân.

5. ⚡ **Giao diện Hiện đại**:
   - SPA (Single Page Application) siêu mượt mà xây dựng trên Vite + React.
   - Hệ thống UI Components cao cấp từ `shadcn/ui` và `Tailwind CSS`.
   - Chế độ Sáng/Tối (Dark/Light mode).

---

## 🏗️ Kiến trúc Hệ thống (Architecture)

Hệ thống được thiết kế theo kiến trúc **Monolithic (FastAPI Host)** để dễ dàng triển khai.

- **Frontend:** React 18, Vite, Tailwind CSS, shadcn/ui, Zustand (State Management), React-Router, React-Leaflet, Recharts.
- **Backend:** FastAPI (Python), SQLAlchemy (ORM), Pydantic, SlowAPI (Rate Limiting).
- **AI/LLM:** Hỗ trợ linh hoạt Ollama (Local LLM), Google Gemini, và công nghệ RAG với ChromaDB / Weaviate / pgvector.
- **Database & Cache:** PostgreSQL (Supabase/Neon), SQLite (Local Fallback), Redis (Caching API & Rate Limit).
- **Deployment:** Multi-stage Docker Build (Node.js -> Python), tích hợp CI/CD Github Actions, sẵn sàng lên Railway, Vercel, Render.

---

## 🚀 Khởi động Dự án (Local Development)

### Cách 1: Chạy bằng Docker (Khuyên dùng)
Yêu cầu đã cài đặt `Docker` và `docker-compose`.

```bash
# Xây dựng và khởi động toàn bộ hệ thống (API, Database, Redis, Frontend)
docker-compose up -d --build
```
Hệ thống sẽ chạy tại: **http://localhost:8000**

### Cách 2: Chạy Thủ công (Manual Setup)

**1. Khởi động Frontend (React)**
```bash
cd frontend
npm install
npm run dev
```

**2. Khởi động Backend (FastAPI)**
```bash
# Kích hoạt môi trường ảo (Tuỳ chọn)
python -m venv venv
venv\Scripts\activate  # Windows

# Cài đặt thư viện
pip install -r requirements.txt

# Khởi động Server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📦 Cấu trúc Thư mục

```text
complete-ai-local/
├── main.py                 # Điểm vào (Entry point) của FastAPI
├── config.py               # Quản lý biến môi trường (Settings)
├── routers/                # Các Endpoints API (auth, rag, maps, learning...)
├── services/               # Logic nghiệp vụ, tích hợp LLM, TTS
├── database.py             # Cấu hình kết nối DB (SQLAlchemy)
├── models.py               # Định nghĩa các Bảng CSDL (User, Route, Event...)
├── Dockerfile              # Script đóng gói Multi-stage Docker
├── docker-compose.yml      # Cấu hình containerization
└── frontend/               # Mã nguồn React SPA
    ├── src/
    │   ├── pages/          # Home, MapPage, AdminDashboard...
    │   ├── components/     # UI Components (shadcn)
    │   ├── store/          # Zustand State (chatStore)
    │   └── services/       # Axios API client
    ├── package.json
    └── vite.config.ts
```

---

## 🌐 Triển khai (Deployment)

Hệ thống được thiết kế tối ưu nhất để chạy tách biệt Frontend trên **Vercel** và Backend trên **Render**.

### Tùy chọn 1: Deploy Bấm 1 chạm (Khuyên dùng)

**Bước 1: Triển khai Backend (Render.com)**
Bấm vào nút dưới đây để tạo tự động API Backend (Miễn phí):

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

*(Sau khi deploy thành công, hãy copy URL của Backend, ví dụ: `https://gtcc-bot-api.onrender.com`)*

**Bước 2: Triển khai Frontend (Vercel)**
Bấm nút dưới đây để triển khai giao diện:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Ftranquangthanh3062004%2Fcomplete-ai-local)

👉 **Lưu ý quan trọng**: Khi Vercel hỏi biến môi trường (Environment Variables), hãy thêm biến:
- `VITE_API_URL` = `[URL Backend của bạn ở Bước 1]`

---

### Tùy chọn 2: Triển khai thủ công qua Github Actions (CI/CD)
1. Fork / Clone repository này.
2. Thiết lập biến môi trường `RAILWAY_TOKEN` trong Settings > Secrets and variables > Actions của Github.
3. Push code lên nhánh `main`, Github Action (`.github/workflows/deploy.yml`) sẽ tự động biên dịch và triển khai dự án.

### Triển khai thủ công lên Railway
```bash
npm i -g @railway/cli
railway login
railway link
railway up --detach
```

---

## ⚙️ Biến Môi trường (.env)

Tạo file `.env` tại thư mục gốc với cấu hình tối thiểu:

```env
# Database
DATABASE_URL="sqlite+aiosqlite:///./test.db"  # Hoặc PostgreSQL URL
SECRET_KEY="your-super-secret-jwt-key"

# AI/LLM
GEMINI_API_KEY="your-google-gemini-key"
LLM_MODEL_NAME="gemini-1.5-flash"

# OAuth (Tuỳ chọn)
GOOGLE_CLIENT_ID="your-google-oauth-client-id"
GOOGLE_CLIENT_SECRET="your-google-oauth-client-secret"
```

---

## 📄 Tài liệu API (Swagger)

Sau khi khởi động Backend, truy cập tài liệu API tương tác tại:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

---
*Phát triển với ❤️ cho hệ thống Giao Thông Công Cộng hiện đại.*