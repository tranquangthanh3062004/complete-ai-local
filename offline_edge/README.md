# Offline Edge Module

Đây là module dành riêng cho thiết bị đặt tại trạm xe buýt (Kiosk). Nó đóng vai trò là API Gateway để định tuyến (route) các yêu cầu dựa trên kết nối mạng.

## Yêu cầu Hệ thống (Cho máy Edge)
- **RAM**: Tối thiểu 4GB (Khuyến nghị 8GB)
- **OS**: Windows / Linux / macOS
- Đã cài đặt **Python 3.10+**
- Đã cài đặt **Ollama**

## Hướng dẫn Cài đặt

1. **Cài đặt Ollama và tải Model**:
   - Truy cập [Ollama.com](https://ollama.com) để cài đặt.
   - Mở Terminal và chạy lệnh tải model:
     ```bash
     ollama run qwen2.5:3b
     ```
     *(Đây là mô hình rất nhẹ, tốn khoảng 1.9GB RAM, cực kỳ tối ưu cho tiếng Việt).*

2. **Cài đặt thư viện Python**:
   - Khuyến nghị tạo một môi trường ảo (`venv`) riêng.
   ```bash
   pip install fastapi uvicorn httpx
   ```

3. **Khởi chạy Edge Gateway**:
   ```bash
   python edge_gateway.py
   ```
   Gateway sẽ chạy ở cổng `8080`.

## Cách hoạt động
- Trình duyệt/UI của Kiosk (chạy React) sẽ gọi API tới `http://localhost:8080/api/chat`.
- File `edge_gateway.py` sẽ ping `1.1.1.1` để kiểm tra mạng.
- **Nếu CÓ mạng**: Chuyển request lên Cloud Backend (`http://your-cloud-ip/api/chat`).
- **Nếu MẤT mạng**: Gửi request thẳng vào mô hình `qwen2.5:3b` đang chạy ngầm trên Ollama thông qua endpoint `http://localhost:11434`.
