# GTCC Bot - Architecture & Technical Blueprint

## 1. Overview
GTCC Bot là hệ thống Chatbot AI hỗ trợ giao thông công cộng tại Việt Nam, tích hợp khả năng tìm kiếm tuyến đường đa phương tiện (Smart Transport) và tra cứu RAG (Retrieval-Augmented Generation) thông tin luật, vé, lịch trình.

## 2. Core Components

### 2.1. Backend (FastAPI)
- **Framework**: FastAPI (Asynchronous)
- **Database**: SQLAlchemy (SQLite for Local, PostgreSQL for Production/Railway)
- **LLM Engine**: LangChain (Hỗ trợ Ollama, Groq, Gemini)
- **Streaming**: Trả về dữ liệu kiểu SSE (Server-Sent Events) qua `/agents/stream` để tăng trải nghiệm UX, loại bỏ độ trễ của API calls.
- **Smart Transport**: Sử dụng thư viện `networkx` trong `services/route_planner.py` tính toán lộ trình ngắn nhất (Dijkstra) kết hợp Metro, Bus, Xe đạp chia sẻ.
- **Vector Store**: Hỗ trợ Pinecone / Supabase pgvector cho dữ liệu văn bản. Fallback về model local của HuggingFace nếu không có API Key.

### 2.2. Frontend (Streamlit)
- Giao diện UI tùy biến với CSS.
- Quản lý session qua `st.session_state`.
- Chế độ hiển thị streaming text qua `st.write_stream`.

### 2.3. Caching Strategy
- **Layer 1: Semantic Cache (Vector Similarity)**
  Lưu các truy vấn tương đồng ý nghĩa (Cosine Similarity > 0.92) để tăng tốc độ phản hồi cho các câu hỏi thường gặp mà không cần gọi LLM.
- **Layer 2: Exact Match TTL Cache**
  Sử dụng `TTLCache` in-memory.

## 3. Security
- Tích hợp xác thực token (JWT).
- Validation upload file bằng chữ ký số (Magic bytes) thay vì kiểm tra đuôi mở rộng, chống upload malware.
- Rate limiter: 20 request/phút/IP để chống spam.

## 4. DevOps & Deployment
- 2 file Dockerfile tách biệt cho Frontend và Backend.
- `railway.toml` cấu hình tự động parse DB URL khi deploy lên nền tảng đám mây.
- CI/CD shell script tích hợp (`ci_test.sh`).
