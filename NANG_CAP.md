# 🚀 NÂNG CẤP HỆ THỐNG GTCC Bot — Lộ Trình Hoàn Thiện

## ⭐ ƯU TIÊN CAO (Làm ngay)

### 1. Bổ sung dữ liệu GTCC thực tế
- [ ] Download lịch trình xe buýt PDF từ Transerco / TTQLGTCC TP.HCM
- [ ] Tải file PDF luật giao thông (Luật GT Đường Bộ 2008, NĐ 100/2019)
- [ ] Thêm bản đồ tuyến xe buýt dạng text/CSV
- **Cách làm:** Đặt file vào `data/` rồi chạy `python ingest_all.py`

### 2. Fine-tune model riêng cho GTCC
- [ ] Thu thập 500-1000 cặp Q&A về GTCC Việt Nam
- [ ] Fine-tune Qwen2.5 hoặc Llama3.2 trên Google Colab (Unsloth)
- [ ] Convert sang GGUF và import vào Ollama
- [ ] Xem hướng dẫn: `FINETUNE_GUIDE.md`

### 3. Tích hợp API thời gian thực
```python
# API BusMap / OpenData HCM
GET https://opendata.hochiminhcity.gov.vn/bus-routes
```
- [ ] Giờ xe thực tế (real-time ETA)
- [ ] Hiển thị bản đồ tuyến đường dùng Folium

---

## 🔶 ƯU TIÊN TRUNG BÌNH (1-2 tuần)

### 4. Tìm lộ trình GTCC
```python
@router.post("/find-route")
async def find_route(origin: str, destination: str):
    # Tính lộ trình kết hợp xe buýt + metro
```

### 5. Bản đồ tương tác
```python
import folium, streamlit_folium
m = folium.Map(location=[10.8231, 106.6297], zoom_start=12)
```

### 6. Đa ngôn ngữ (tiếng Anh cho du khách)
```python
from langdetect import detect
lang = detect(user_query)
```

### 7. Redis cache câu trả lời phổ biến
```python
import redis
r = redis.Redis()
cached = r.get(f"gtcc:{hash(query)}")
```

---

## 🔹 ƯU TIÊN THẤP (Dài hạn)

### 8. Voice Chat (giọng nói)
```python
import speech_recognition as sr
r = sr.Recognizer()
text = r.recognize_google(audio, language="vi-VN")
```

### 9. Telegram / Zalo Bot
```python
from telegram.ext import Application, MessageHandler
app = Application.builder().token(TOKEN).build()
```

### 10. Mobile App (GPS tìm trạm gần nhất)

### 11. Dashboard Admin GTCC

---

## 🛠️ BUG & CẢI TIẾN KỸ THUẬT

- [ ] Retry logic khi Ollama timeout
- [ ] Rate limiting (5 req/phút/user)
- [ ] Input sanitization (chặn prompt injection)
- [ ] Unit test cho routers GTCC
- [ ] HTTPS production (nginx + certbot)

---

## 📊 NGUỒN DỮ LIỆU GTCC GỢI Ý

| Nguồn | Loại | URL |
|-------|------|-----|
| Transerco Hà Nội | Lịch trình, tuyến | transerco.com.vn |
| TTQLGTCC TP.HCM | Xe buýt, vé | buyttphcm.com.vn |
| Metro TP.HCM | Tuyến số 1 | metro.hochiminhcity.gov.vn |
| Metro Hà Nội | Tuyến 2A | mrhanoi.gov.vn |
| OpenData HCM | Data mở | opendata.hochiminhcity.gov.vn |

---

## 🎯 LỘ TRÌNH ĐỀ XUẤT

```
Tuần 1-2: Bổ sung dữ liệu GTCC thực tế (PDF, CSV)
Tuần 3-4: Tích hợp bản đồ Folium
Tháng 2:  Fine-tune model GTCC riêng
Tháng 3:  API thời gian thực + voice chat
Tháng 4+: Mobile app, Telegram/Zalo bot
```

---
*GTCC Bot v4.0 | Cập nhật: 2026-05-13*
