# 🗺️ Sơ Đồ Hệ Thống GTCC Bot & Mạng Lưới Giao Thông Công Cộng VN

---

## 1. Kiến Trúc Hệ Thống GTCC Bot

```mermaid
graph TB
    USER["👤 Người dùng\n(Trình duyệt)"]
    
    subgraph FRONTEND["🖥️ Frontend - Streamlit :8501"]
        UI_CHAT["💬 Tab Chat\nHỏi đáp trực tiếp"]
        UI_RAG["📚 Tab RAG\nHỏi tài liệu"]
        UI_ANALYTICS["📊 Tab Analytics\nPhân tích học tập"]
        UI_DOCS["📁 Tab Tài liệu\nQuản lý PDF"]
    end

    subgraph BACKEND["⚙️ Backend - FastAPI :8000"]
        AUTH["🔐 /auth\nJWT Authentication"]
        RAG_API["🔍 /documents\nRAG + Vector Search"]
        AGENT_API["🤖 /agents\nChat + Tools"]
        LEARN_API["📈 /learning\nTracking & Analytics"]
    end

    subgraph AI_LAYER["🧠 AI Layer"]
        OLLAMA["🦙 Ollama\nlocalhost:11434\nllama3:latest / qwen / phi3"]
        EMBED["🔢 Embeddings\nvietnamese-sbert\nHuggingFace Local"]
    end

    subgraph STORAGE["💾 Lưu trữ Local"]
        SQLITE[("🗃️ SQLite\ncompleteai.db\nUsers, Events, Mastery")]
        CHROMA[("🎨 ChromaDB\nchroma_db/\nVector Store")]
        FILES["📄 Files\ndata/\ngtcc_kienthuc.txt\nPDF uploads"]
    end

    USER --> FRONTEND
    FRONTEND --> BACKEND
    AUTH --> SQLITE
    RAG_API --> CHROMA
    RAG_API --> OLLAMA
    RAG_API --> EMBED
    AGENT_API --> OLLAMA
    LEARN_API --> SQLITE
    EMBED --> CHROMA
    FILES --> EMBED
```

---

## 2. Luồng Xử Lý Câu Hỏi RAG

```mermaid
sequenceDiagram
    participant U as 👤 Người dùng
    participant F as 🖥️ Streamlit
    participant B as ⚙️ FastAPI
    participant C as 🎨 ChromaDB
    participant O as 🦙 Ollama LLM

    U->>F: Gõ câu hỏi về GTCC
    F->>B: POST /documents/chat
    B->>B: Phát hiện chủ đề (topic detection)
    B->>C: Tìm kiếm vector similarity (top-6)
    C-->>B: Trả về 6 đoạn văn liên quan
    B->>O: Gửi prompt = Context + Câu hỏi
    O-->>B: Sinh câu trả lời tiếng Việt
    B->>B: Lưu LearningEvent vào SQLite
    B-->>F: Trả về {answer, sources, topic, event_id}
    F-->>U: Hiển thị câu trả lời + nguồn trích dẫn + nút 👍👎
    U->>F: Nhấn 👍 hoặc 👎
    F->>B: POST /learning/feedback
    B->>B: Cập nhật TopicMastery score
```

---

## 3. Luồng Upload & Index Tài Liệu

```mermaid
flowchart LR
    A["📁 File PDF/TXT/DOCX\nUpload từ giao diện"] --> B["🔄 Document Loader\nPyPDF / TextLoader"]
    B --> C["✂️ Text Splitter\nChunk size 1000\nOverlap 200"]
    C --> D["🔢 Embedding\nVietnamese SBERT\nHuggingFace Local"]
    D --> E[("🎨 ChromaDB\nVector Store\nPersist to disk")]
    E --> F["✅ Index xong!\nSẵn sàng trả lời"]
```

---

## 4. Hệ Thống Cá Nhân Hóa Học Tập

```mermaid
graph TD
    Q["❓ Câu hỏi của user"] --> TD["🏷️ Topic Detection\nPhát hiện chủ đề:\nluật / kỹ thuật / toan /\ny tế / kinh tế / gtcc"]
    TD --> ANS["🤖 Trả lời"]
    ANS --> LE["📝 LearningEvent\n- user_id\n- question\n- topic\n- response_time_ms\n- model_used"]
    LE --> FB["👍👎 Feedback"]
    FB --> TM["📊 TopicMastery\n- mastery_score 0.0→1.0\n- total_questions\n- positive/negative"]
    TM --> PROFILE["👤 Hồ sơ học tập\nĐiểm mạnh / Điểm yếu"]
    PROFILE --> RADAR["📡 Biểu đồ Radar\nStreamlit Analytics Tab"]
```

---

## 5. Sơ Đồ Mạng Lưới Metro TP.HCM

```
BẾN THÀNH ●────────────────────────────────────────────● SUỐI TIÊN
(Metro 1)  │                                            │
  Q.1      Ba Son ─ Văn Thánh ─ Tân Cảng ─ Thảo Điền  Bình Dương ─ Tân Phú ─ CNC ─ Thủ Đức ─ Bình Thái ─ Phước Long ─ Rạch Chiếc ─ An Phú
           [Ngầm]   [Ngầm]     [Trên cao] ...........  ................................................. [Trên cao]

KÝ HIỆU:
  ● = Ga cuối tuyến
  ─ = Ga trên cao
  [Ngầm] = Ga dưới lòng đất
  * = Điểm kết nối metro tương lai

Khoảng cách tổng: 19,7 km | Thời gian: ~30 phút | 14 ga
```

```mermaid
graph LR
    BT["🚇 Bến Thành\n[Ngầm B3]\n★ Hub chính"]
    BS["Ba Son\n[Ngầm]"]
    VT["Văn Thánh\n[Ngầm]"]
    TC["Tân Cảng\n▲ Trên cao"]
    TD["Thảo Điền\n▲"]
    AP["An Phú\n▲ AEON"]
    RC["Rạch Chiếc\n▲"]
    PL["Phước Long\n▲"]
    BT2["Bình Thái\n▲"]
    TDu["Thủ Đức\n▲ ĐH QG"]
    CNC["KHU CNC\n▲ SHTP"]
    TP["Tân Phú\n▲"]
    BD["Bình Dương\n▲"]
    ST["🏁 Suối Tiên\n▲ Hub cuối"]

    BT --> BS --> VT --> TC --> TD --> AP --> RC --> PL --> BT2 --> TDu --> CNC --> TP --> BD --> ST
```

---

## 6. Sơ Đồ Metro Hà Nội

```mermaid
graph LR
    subgraph "Tuyến 2A — Cát Linh – Hà Đông (13km, Đang hoạt động)"
        CL["Cát Linh"] --> LT["La Thành"] --> TH["Thái Hà"] --> LA["Láng"] --> TDinh["Thượng Đình"] --> VD3["Vành Đai 3"] --> PK["Phùng Khoang"] --> VQ["Văn Quán"] --> HD["Hà Đông"] --> LK["La Khê"] --> VKhe["Văn Khê"] --> YN["Yên Nghĩa\n🔵 Kết nối BRT"]
    end

    subgraph "Tuyến 3 — Nhổn – Ga Hà Nội (12,5km)"
        N["Nhổn\n✅ Đang chạy"] --> MK["Minh Khai\n✅"] --> PD["Phú Diễn\n✅"] --> CD["Cầu Diễn\n✅"] --> LDT["Lê Đức Thọ\n✅"] --> DHQG["ĐH QG\n✅"] --> CH["Chùa Hà\n✅"] --> CG["Cầu Giấy\n✅ Điểm chuyển"] --> KM["Kim Mã\n🔨 2027"] --> CL2["Cát Linh\n🔨 2027\n↕ Kết nối T.2A"] --> VM["Văn Miếu\n🔨 2027"] --> GHN["Ga Hà Nội\n🔨 2027"]
    end
```

---

## 7. Sơ Đồ Kết Nối Metro – Xe Buýt TP.HCM

```mermaid
graph TD
    subgraph "Metro Số 1 (Đang hoạt động)"
        M1_BT["Ga Bến Thành"] 
        M1_AN["Ga An Phú"]
        M1_TDu["Ga Thủ Đức"]
        M1_ST["Ga Suối Tiên"]
    end

    subgraph "Xe Buýt Kết Nối"
        B152["🚌 Buýt 152\nSân bay TSN"]
        B36["🚌 Buýt 36\nBến Thành↔ĐHQG"]
        BE158["⚡ Buýt điện 158\nGa Thủ Đức→ĐHQG"]
        BE167["⚡ Buýt điện 167\nGa Suối Tiên→Long Bình"]
        B60["🚌 Buýt 60\nBX Miền Đông mới"]
    end

    B152 --> M1_BT
    M1_BT --> B36
    M1_TDu --> BE158
    M1_ST --> BE167
    M1_ST --> B60
    BE158 --> DHQG["🎓 ĐH Quốc gia\nTP.HCM"]
```

---

## 8. Biểu Đồ So Sánh Giá Vé GTCC

```
GIÁ VÉ LƯỢT (đồng)

Metro TP.HCM (0–4km)  ████ 6,000
Metro TP.HCM (toàn)   ████████████████████ 20,000
Metro HN (Cát Linh)   ████████ 8,000 – 15,000
Metro HN (Tuyến 3)    ████████ 8,000 – 15,000
Buýt điện TSN (SV)    ███ 3,000
Buýt điện TSN         █████ 5,000 – 6,000
Buýt TP.HCM ngắn      █████ 5,000
Buýt TP.HCM dài       ████████ 7,000 – 8,000
Buýt Hà Nội (<15km)   ████████ 8,000
Buýt Hà Nội (>40km)   ████████████████████ 20,000
Buýt sông TP.HCM      ███████████████ 15,000
BRT Hà Nội            ████████ 9,000
```

---

## 9. Biểu Đồ Giờ Hoạt Động

```
Hệ thống         | 04 | 05 | 06 | 07 | 08 | ... | 21 | 22 | 23
─────────────────|────|────|────|────|────|─────|────|────|────
Metro 1 TP.HCM   |    | ██ | ██ | ██ | ██ | ██  | ██ | ██ |
Metro 2A HN      |    | ██ | ██ | ██ | ██ | ██  | ██ | ██ | ██
Metro 3 HN       |    | ██ | ██ | ██ | ██ | ██  | ██ | ██ |
Buýt HCM (nhiều) | ██ | ██ | ██ | ██ | ██ | ██  | ██ |    |
Buýt HN (nhiều)  |    | ██ | ██ | ██ | ██ | ██  | ██ |    |
BRT HN           | ██ | ██ | ██ | ██ | ██ | ██  | ██ | ██ |
Buýt sông HCM    |    | ██ | ██ | ██ | ██ | ██  | ██ |    |
```

---

## 10. Cấu Trúc Database

```mermaid
erDiagram
    USER {
        int id PK
        string email
        string hashed_password
        string display_name
        string role
        bool is_active
        bool is_superuser
    }
    
    DOCUMENT {
        int id PK
        int user_id FK
        string filename
        string content
        datetime created_at
    }
    
    LEARNINGEVENT {
        int id PK
        int user_id FK
        string session_id
        string question
        string answer
        string topic
        float response_time_ms
        string model_used
        int feedback
        datetime created_at
    }
    
    TOPICMASTERY {
        int id PK
        int user_id FK
        string topic
        int total_questions
        int positive_feedback
        int negative_feedback
        float mastery_score
        datetime last_updated
    }

    USER ||--o{ DOCUMENT : "uploads"
    USER ||--o{ LEARNINGEVENT : "asks"
    USER ||--o{ TOPICMASTERY : "has"
```

---

## 11. Luồng Khởi Động Hệ Thống

```mermaid
flowchart TD
    START["▶️ Chạy START.bat"] --> OLLAMA["🔍 Kiểm tra Ollama\n(ollama serve)"]
    OLLAMA --> CHECK_MODEL["📥 Kiểm tra model\nllama3:latest có chưa?"]
    CHECK_MODEL -->|Chưa có| PULL["⬇️ ollama pull llama3:latest"]
    CHECK_MODEL -->|Đã có| VENV["🐍 Kích hoạt venv"]
    PULL --> VENV
    VENV --> BACKEND["⚙️ uvicorn main:app\n--port 8000\n(Cửa sổ riêng)"]
    BACKEND --> DB_INIT["🗃️ Khởi tạo DB\nTạo bảng SQLite\nSeed admin user"]
    DB_INIT --> FRONTEND["🖥️ streamlit run app.py\n--port 8501\n(Cửa sổ riêng)"]
    FRONTEND --> BROWSER["🌐 Mở trình duyệt\nhttp://localhost:8501"]
    BROWSER --> READY["✅ Hệ thống sẵn sàng!\nĐăng nhập: admin@local.com"]
```

---

*Tài liệu: GTCC Bot System Diagrams v3.0 | Cập nhật: 2026-05*
