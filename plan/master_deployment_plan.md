# TỔNG HỢP KẾ HOẠCH TRIỂN KHAI CLOUD NATIVE & CHI PHÍ - GTCC BOT

Tài liệu này tổng hợp toàn bộ lộ trình, kiến trúc, và dự toán để sẵn sàng vận hành hệ thống Chatbot Giao thông công cộng Việt Nam lên môi trường Web Production (Miễn phí 100%).

## 1. Kiến Trúc Hệ Thống (Cloud Native Microservices)

Hệ thống được chuyển đổi từ mô hình Local (Ollama + SQLite) sang kiến trúc Cloud phân tán, nhằm tận dụng tối đa các dịch vụ Free Tier của thế giới:

- **Frontend:** `Streamlit Community Cloud` (Xử lý giao diện người dùng, zero-cost, siêu nhanh).
- **Backend:** `Render` hoặc `Koyeb` (FastAPI Web Service - Xử lý logic API RAG và Agents).
- **Database (Auth + Logs):** `Supabase PostgreSQL` (Lưu trữ user, lịch sử chat và tích hợp đăng nhập Google/Github).
- **Vector Database:** `Supabase pgvector` (Lưu các đoạn tài liệu chunk của GTCC - thay thế cho ChromaDB).
- **AI LLM Engine:** `Groq API` (Llama 3/3.2 siêu tốc độ, miễn phí 14.400 request/ngày) hoặc `Gemini API`.
- **Embeddings AI:** `Google Gemini Embedding API` hoặc `HuggingFace Inference API`.

## 2. Tiến Độ Thực Hiện

✅ **Pha 1: Refactor Cấu trúc Local**
- Cập nhật `.env` hỗ trợ đa model (Groq, Gemini, Ollama).
- Thêm hệ thống Logging ra file `gtcc_bot.log`.
- Giao diện (UI) chuyển sang Light Mode cực đẹp như ChatGPT.

✅ **Pha 2: Nâng cấp Backend tương thích Cloud**
- Sửa `database.py` dùng PostgreSQL (SQLAlchemy + asyncpg).
- Sửa `rag.py` dùng `SupabaseVectorStore`.
- Sửa `llm_factory.py` gọi API Groq/Gemini thông qua LangChain.

🔜 **Pha 3 & 4: Deploy & Auth**
- Cần tạo Project trên Supabase và lấy API Key.
- Deploy Frontend lên Streamlit Cloud, trỏ Backend vào URL của Render.

## 3. Dự Toán Chi Phí

- **Mặc định:** $0 / tháng.
- **Phát sinh 1 (Máy chủ Render ngủ sau 15p):** $7 / tháng (Nâng cấp Render để server chạy 24/7).
- **Phát sinh 2 (Quá 30 câu hỏi / phút):** Nạp Pay-as-you-go cho Groq (~60.000 VNĐ cho 100.000 câu hỏi).
- **Phát sinh 3 (Đầy bộ nhớ DB):** $25 / tháng (Nâng cấp Supabase Pro lên 8GB nếu có quá nhiều file tài liệu tải lên).

---
*(Bản tổng hợp hoàn chỉnh này lưu tại `/plan/master_deployment_plan.md`)*
