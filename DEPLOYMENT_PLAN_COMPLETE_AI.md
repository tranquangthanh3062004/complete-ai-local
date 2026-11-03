# KẾ HOẠCH TRIỂN KHAI PRODUCTION — COMPLETE AI v5.10.0
**Dự án:** COMPLETE AI — Hệ thống Trợ lý Trí tuệ Nhân tạo Giao Thông Công Cộng Việt Nam  
**Phiên bản:** `v5.10.0 (Release Candidate)`  
**Tác giả:** Đội ngũ Kỹ thuật COMPLETE AI  
**Cập nhật lần cuối:** 03/11/2026  

---

## 1. TỔNG QUAN KIẾN TRÚC TRIỂN KHAI (DEPLOYMENT TOPOLOGY)

Hệ thống COMPLETE AI hỗ trợ linh hoạt 3 mô hình triển khai chuẩn doanh nghiệp:

```mermaid
flowchart TD
    subgraph ClientLayer["1. Client Layer"]
        WebUser["Người dùng Web / Mobile"]
        KioskUser["Hành khách tại Nhà ga Kiosk"]
    end

    subgraph EdgeLayer["2. Edge / Kiosk Layer (Cục bộ không cần Internet)"]
        EdgeKiosk["Kiosk Hardware (Intel NUC / mini PC)"]
        EdgeGateway["COMPLETE AI Edge Gateway (:8080)"]
        LocalOllama["Local LLM Ollama (qwen2.5:3b)"]
        LocalChroma["ChromaDB Vector Knowledge (17 docs)"]
        EdgeKiosk --> EdgeGateway
        EdgeGateway --> LocalOllama
        EdgeGateway --> LocalChroma
    end

    subgraph CloudLayer["3. Cloud Production Cluster"]
        CDN["Vercel Edge Network / Cloudflare CDN"]
        FrontendSPA["React 18 Single Page Application"]
        BackendAPI["FastAPI Production Service (:8000)"]
        
        CDN --> FrontendSPA
        FrontendSPA --> BackendAPI
        
        subgraph DataTier["Data & AI Tier"]
            PostgreSQL["PostgreSQL 16 (Supabase / Neon DB)"]
            CloudLLM["Cloud AI Engine (Google Gemini / Groq)"]
            OSRM_Service["OSRM & Nominatim Routing Engine"]
        end
        
        BackendAPI --> PostgreSQL
        BackendAPI --> CloudLLM
        BackendAPI --> OSRM_Service
    end

    WebUser --> CDN
    KioskUser --> EdgeKiosk
    EdgeGateway -. "Khi có mạng Internet (Sync)" .-> BackendAPI
```

---

## 2. MA TRẬN BIẾN MÔI TRƯỜNG (PRODUCTION ENVIRONMENT MATRIX)

Tất cả các biến môi trường được quản lý qua Secret Manager của nền tảng Cloud (không commit file `.env` lên GitHub):

| Tên biến | Bắt buộc | Mô tả & Giá trị mẫu | Môi trường áp dụng |
|----------|----------|----------------------|-------------------|
| `APP_NAME` | Có | `"COMPLETE AI"` | All |
| `APP_VERSION` | Có | `"5.10.0"` | All |
| `OPERATION_MODE` | Có | `online` / `offline` / `hybrid` | Cloud / Edge |
| `DATABASE_URL` | Có | `postgresql+asyncpg://user:pass@host:5432/db` (Local: `sqlite+aiosqlite:///./completeai.db`) | Backend |
| `SECRET_KEY` | Có | Chuỗi ngẫu nhiên 64 ký tự hex (sinh bằng `openssl rand -hex 32`) | Backend |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Không | `1440` (24 giờ) | Backend |
| `LLM_ENGINE` | Có | `gemini` (Cloud chính) hoặc `groq` (Dự phòng) | Backend |
| `LLM_MODEL_NAME` | Có | `gemini-2.5-flash` hoặc `llama-3.3-70b-versatile` | Backend |
| `GEMINI_API_KEY` | Tùy chọn | Khóa API Google AI Studio | Cloud |
| `GROQ_API_KEY` | Tùy chọn | Khóa API Groq Cloud (Tự động fallback khi Gemini quá tải) | Cloud |
| `GOOGLE_MAPS_API_KEY` | Tùy chọn | Khóa Google Maps API (Nếu không có, tự động dùng OSRM miễn phí) | Cloud |
| `CORS_ORIGINS` | Có | Domain Frontend (VD: `https://complete-ai.vercel.app`) | Backend |
| `PORT` | Không | `8000` (FastAPI) | Backend |
| `EDGE_GATEWAY_PORT` | Không | `8080` | Edge Kiosk |

---

## 3. CÁC PHƯƠNG ÁN TRIỂN KHAI CHI TIẾT

### Phương án A: Triển khai Đám mây (Vercel Frontend + Render/Railway Backend) - Khuyên dùng

#### Bước A1: Triển khai Backend (FastAPI) lên Railway hoặc Render
1. Kết nối kho mã nguồn GitHub: `tranquangthanh3062004/complete-ai-local` (nhánh `main`).
2. Nền tảng tự động nhận diện `Dockerfile` hoặc `render.yaml` / `railway.toml`.
3. Điền các Environment Variables theo bảng mục 2.
4. Lệnh chạy (Start Command):
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   ```
5. Endpoint kiểm tra sức khỏe (Health Check Path): `/health`.

#### Bước A2: Triển khai Frontend (React SPA) lên Vercel
1. Import repository vào Vercel, chọn Root Directory là `frontend`.
2. Framework Preset: **Vite**.
3. Build Command: `npm run build`.
4. Output Directory: `dist`.
5. Environment Variable:
   - `VITE_API_URL`: Điền URL Backend vừa triển khai ở Bước A1 (VD: `https://complete-ai-backend.onrender.com`).
6. Deploy hoàn tất: Vercel cung cấp chứng chỉ SSL HTTPS miễn phí toàn cầu.

---

### Phương án B: Triển khai Full-Stack bằng Docker Compose (On-Premise / VPS)

Thích hợp cho máy chủ riêng (Ubuntu/Debian VPS) hoặc môi trường intranet của Sở GTVT:

```bash
# 1. Clone repository
git clone https://github.com/tranquangthanh3062004/complete-ai-local.git
cd complete-ai-local

# 2. Tạo file cấu hình môi trường
cp .env.example .env
nano .env  # Điền SECRET_KEY và API Keys

# 3. Khởi động toàn bộ cụm Container
docker compose up -d --build
```
Hệ thống tự động:
- Build Multi-stage image (Node.js -> Python FastAPI).
- Khởi tạo SQLite / PostgreSQL.
- Mở cổng `8000` cho dịch vụ hoàn chỉnh (bao gồm cả static React frontend).

---

### Phương án C: Triển khai Trạm Kiosk Ngoại tuyến (Edge Station)

Dành cho các máy Kiosk tra cứu tại các nhà ga Metro (Cát Linh, Hà Đông, Nhổn) và bến xe buýt lớn:

1. **Yêu cầu phần cứng:** Mini PC / Raspberry Pi 5 / Intel NUC, RAM 4GB+, SSD 64GB.
2. **Cài đặt Ollama Cục bộ:**
   ```bash
   ollama run qwen2.5:3b
   ```
3. **Chạy Edge Gateway:**
   ```bash
   python offline_edge/edge_gateway.py
   ```
   Gateway chạy độc lập tại cổng `8080`, tự động phục vụ tra cứu tuyến xe, tính toán lộ trình Dijkstra, bảng giá vé mà không cần cắm dây mạng Internet.

---

## 4. CHIẾN LƯỢC QUẢN LÝ DỮ LIỆU & VECTOR STORE (RAG INGESTION)

Khi triển khai trên môi trường mới, thực hiện nạp dữ liệu tri thức giao thông vào CSDL Vector:

```bash
# Nạp toàn bộ dữ liệu văn bản, lịch trình xe buýt, metro Hà Nội & TP.HCM
python ingest_local.py
```
- Sử dụng mô hình `intfloat/multilingual-e5-small` nạp hơn 300 đoạn tài liệu pháp lý, biểu giá vé và hành trình các tuyến buýt vào `chroma_db/`.
- CSDL Vector được phân vùng chỉ mục HNSW cosine distance đảm bảo thời gian truy xuất dưới 15ms.

---

## 5. CI/CD PIPELINE & QUALITY GATE AUTOMATION

Quy trình tự động hóa GitHub Actions được thiết lập để bảo vệ chất lượng nhánh `main`:

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer
    participant Git as GitHub (main / deploy-testing)
    participant CI as GitHub Actions (ci_test.sh)
    participant Sec as Security Sanitizer Scan
    participant Pytest as Pytest Runner (27 Tests)
    participant Cloud as Cloud Production (Render/Vercel)

    Dev->>Git: git push origin main
    Git->>CI: Trigger CI Workflow
    CI->>Sec: Quét Prompt Injection & Vulnerabilities
    Sec-->>CI: OK (100% Blocked)
    CI->>Pytest: Chạy 27 bài kiểm thử hồi quy
    Pytest-->>CI: 27 Passed (100%)
    CI->>Cloud: Tự động kích hoạt Webhook Deploy
    Cloud-->>Dev: Production Live (Ready)
```

**Quality Gate Rules:**
- Bất kỳ commit nào làm fail dù chỉ 1 bài test trong 27 bài test Pytest sẽ lập tức bị chặn deploy.
- Bộ lọc `sanitizer.py` phải chặn đứng 100% các câu hỏi tấn công prompt injection trước khi bản build được phê duyệt.

---

## 6. KẾ HOẠCH PHỤC HỒI THẢM HỌA (DISASTER RECOVERY & ROLLBACK)

| Tình huống sự cố | Giải pháp Tự động | Thao tác Thủ công |
|-------------------|-------------------|-------------------|
| **Google Gemini API hết hạn ngạch (Quota 429)** | Hệ thống tự động chuyển sang Groq Cloud (`llama-3.3-70b`) không gián đoạn | Đổi `LLM_ENGINE=groq` trong cấu hình |
| **Mất kết nối Internet hoàn toàn** | Tự động kích hoạt **Offline Fallback Engine** và Smart Route nội bộ | Chuyển Header `X-Network-Mode: offline` |
| **Bản cập nhật mã nguồn có lỗi phát sinh** | - | Rollback tức thì trên GitHub: `git revert HEAD` hoặc chọn lại bản Deployment trước trên Vercel/Render với 1 click |
| **Cơ sở dữ liệu SQLite gặp lỗi khóa file** | Tự động nới lỏng timeout qua aiosqlite | Xóa file cache tạm, hệ thống tự động tái tạo bảng |

---
*Kế hoạch Triển khai đã được phê duyệt và sẵn sàng áp dụng cho giai đoạn Release Candidate v5.10.0.*
