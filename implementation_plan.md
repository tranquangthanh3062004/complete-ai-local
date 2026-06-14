# Kế hoạch Tối ưu và Triển khai GTCC Bot v5.1

Hệ thống GTCC Bot của bạn đã có cấu trúc khá tốt (chia tách Frontend Streamlit, Backend FastAPI, LLM Factory). Để tối ưu chi phí rẻ nhất (gần như $0) cho 2 hướng triển khai: **Local** và **Sử dụng API Cloud (bên thứ 3)**, tôi đã phân tích và đề xuất các điểm cần cải thiện như sau.

## User Review Required

> [!IMPORTANT]
> Vui lòng xem xét các đề xuất dưới đây và cho tôi biết bạn muốn bắt tay vào chỉnh sửa phần nào trước (ví dụ: cập nhật model Tiếng Việt, thay đổi Database/Vector DB cho Cloud, hay nâng cấp TTS).

## Phân tích các điểm yếu hiện tại
1. **Model Embeddings**: Đang dùng `sentence-transformers/all-MiniLM-L6-v2` mặc định. Đây là model chuyên tiếng Anh, khi tìm kiếm tài liệu GTCC (tiếng Việt) hiệu quả RAG sẽ bị giảm.
2. **Text-to-Speech (TTS)**: `gTTS` nghe khá chậm và kém tự nhiên. Fallback `pyttsx3` nghe rất "robot".
3. **Database & ChromaDB**: Đang lưu file SQLite và ChromaDB trực tiếp vào ổ cứng (`./completeai.db`, `./chroma_db`). Rất tốt cho Local, nhưng không thể deploy lên các dịch vụ Serverless Cloud miễn phí (như Vercel/Render) vì ổ cứng bị reset mỗi lần khởi động.

---

## Proposed Changes: Hướng 1 - Triển Khai Local (Chi phí $0)
*Mục tiêu: Chạy 100% trên máy tính cá nhân hoặc server tự host, hoàn toàn bảo mật, không phụ thuộc internet.*

### 1. Cải thiện Embeddings (Tiếng Việt)
- **Hành động**: Đổi sang `paraphrase-multilingual-MiniLM-L12-v2` hoặc `keepitreal/vietnamese-sbert` (model được fine-tune riêng cho tiếng Việt).
- **Lợi ích**: Tăng độ chính xác (Precision/Recall) lên tới 30-40% khi RAG tài liệu tiếng Việt.

### 2. Tối ưu Ollama LLM
- Khuyên dùng `qwen2.5-7b-instruct` hoặc `llama-3.1-8b-instruct`. 
- Nếu máy tính yếu (RAM < 8GB), dùng `qwen2.5-1.5b-instruct` (cực nhẹ và hiểu tiếng Việt tốt).

### 3. Nâng cấp Giọng nói (TTS) Offline
- **Hành động**: Thay thế `pyttsx3` bằng `Piper TTS` (có model Tiếng Việt mã nguồn mở, chạy CPU mượt mà).
- **Lợi ích**: Giọng tự nhiên hơn rất nhiều so với pyttsx3 mà không cần kết nối mạng.

---

## Proposed Changes: Hướng 2 - Sử dụng API Bên Thứ 3 (Chi phí $0 hoặc cực rẻ)
*Mục tiêu: Đưa lên web cho mọi người dùng, tận dụng các Free Tier hào phóng từ các dịch vụ Cloud.*

### 1. LLM API (Miễn phí)
- **Groq API**: Dùng `llama3-8b-8192` hoặc `llama-3.1-8b-instant`. Rất nhanh và có Free Tier.
- **Gemini API**: Dùng `gemini-1.5-flash`. Hỗ trợ 15 request/phút miễn phí, context window siêu lớn (hỗ trợ đẩy nguyên tài liệu PDF vào chat mà không cần RAG nếu tài liệu nhỏ).

### 2. Database và Vector DB (Free Tier)
- **Vấn đề**: SQLite và ChromaDB lưu file local không chạy được trên Cloud Serverless.
- **Hành động**: 
  - **Database**: Dùng `Supabase` (miễn phí 500MB PostgreSQL DB). `config.py` của bạn đã có biến `supabase_url`, ta cần hoàn thiện kết nối.
  - **Vector DB**: Chuyển từ ChromaDB sang `Pinecone` (Miễn phí 1 Index) hoặc dùng thẳng `pgvector` trên Supabase (Để gộp chung với DB, tiết kiệm công quản lý).

### 3. Nâng cấp TTS API (Miễn phí & Cực hay)
- **Hành động**: Đổi từ `gTTS` sang thư viện `edge-tts` (Sử dụng API ẩn của Microsoft Edge Read Aloud).
- **Lợi ích**: Hoàn toàn miễn phí, tốc độ cao, giọng Tiếng Việt (Hoài My, Nam Minh) nghe tự nhiên, ấm và ngắt nghỉ chuẩn hơn gTTS rất nhiều.

### 4. Hosting (Miễn phí)
- **Frontend (Streamlit)**: Deploy lên `Streamlit Community Cloud`.
- **Backend (FastAPI)**: Deploy lên `Render` (Web Service - Free) hoặc `Koyeb`.

---

## Chi tiết các File cần thay đổi (Bước tiếp theo)

Nếu bạn đồng ý, tôi sẽ tiến hành sửa các file sau:

#### [MODIFY] `config.py`
- Tách file config để dễ dàng switch giữa cấu hình `local` và `cloud`. Đổi embedding model sang multi-lingual.

#### [MODIFY] `services/tts_service.py`
- Thêm `edge-tts` thay thế cho gTTS làm tùy chọn online ưu tiên, nâng cấp chất lượng giọng đọc.

#### [MODIFY] (Tùy chọn) `database.py` & Vector Store logic
- Bổ sung logic kết nối Supabase Postgres hoặc Pinecone để sẵn sàng cho môi trường Cloud serverless.

## Open Questions
1. Bạn muốn ưu tiên triển khai mô hình **Local** trước hay thiết lập cho **Cloud API** trước?
2. Bạn có muốn đổi TTS sang `edge-tts` (Microsoft) để có giọng đọc tự nhiên hơn ngay bây giờ không?
3. Về cấu hình Cloud, bạn đã đăng ký tài khoản Supabase (Database) hay Pinecone (VectorDB) nào chưa, hay vẫn đang ở bước lên kế hoạch?
