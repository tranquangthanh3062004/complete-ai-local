import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
import uvicorn
try:
    from offline_edge.edge_rag import search_offline_knowledge
except ImportError:
    from edge_rag import search_offline_knowledge

app = FastAPI(title="COMPLETE AI Edge Gateway (Offline Mode)")

# Cấu hình
CLOUD_API_URL = os.getenv("CLOUD_API_URL", "http://localhost:8000/api")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "qwen2.5:3b")

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """
    Gateway định tuyến.
    Thực tế: UI Kiosk sẽ gọi vào đây. File này sẽ chạy PING để xem có mạng không.
    - Nếu CÓ MẠNG: forward request lên Cloud.
    - Nếu MẤT MẠNG: tự gọi vào Offline RAG + Local Ollama / Smart Route Fallback.
    """
    data = await request.json()
    prompt = data.get("message", data.get("query", ""))
    
    # 1. Kiểm tra mạng nhanh
    is_online = False
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.head("https://1.1.1.1")
            is_online = resp.status_code == 200
    except Exception:
        is_online = False

    # 2. Xử lý Online
    if is_online:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                cloud_resp = await client.post(f"{CLOUD_API_URL}/agents/direct", json={"query": prompt})
                if cloud_resp.status_code == 200:
                    return JSONResponse(content=cloud_resp.json(), status_code=cloud_resp.status_code)
        except Exception:
            print("[Edge Gateway] Cloud timeout or unavailable, fallback to offline mode.")

    # 3. Xử lý Offline
    try:
        # Lấy context từ VectorDB local
        offline_context = search_offline_knowledge(prompt, n_results=4)
        
        # Kiểm tra nếu là câu hỏi tìm đường -> gọi Smart Route Offline
        import sys
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from services.langgraph_agent import extract_locations_and_intent_regex
        requires_map, _, orig, dest, _ = extract_locations_and_intent_regex(prompt)
        
        route_str = ""
        if requires_map and dest:
            try:
                from services.smart_route import find_multiple_routes
                orig_name = orig if orig else "Ga Hà Nội"
                routes = find_multiple_routes(orig_name, dest, city="HN")
                if routes:
                    r = routes[0]
                    t_mins = r.get('total_time_mins', r.get('total_time', 0))
                    cost_val = r.get('total_cost', r.get('total_cost_vnd', 0))
                    route_str = f"\n\n🗺️ **Lộ trình Offline ước tính:**\n- Từ: {r['origin']} → Đến: {r['destination']}\n- Thời gian: ~{t_mins} phút | Chi phí: {cost_val:,}đ\n"
            except Exception as e:
                print(f"[Edge Offline Route Error] {e}")

        system_prompt = (
            "Bạn là COMPLETE AI (Chế độ Ngoại tuyến). "
            "Trả lời ngắn gọn, lịch sự bằng Tiếng Việt dựa trên thông tin sẵn có."
        )
        if offline_context:
            system_prompt += f"\n\nKIẾN THỨC NGOẠI TUYẾN:\n{offline_context}"
            
        full_prompt = f"{system_prompt}\n\nNgười dùng: {prompt}\n COMPLETE AI:"
        
        # Thử gọi Local Ollama
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                ollama_resp = await client.post(
                    OLLAMA_URL,
                    json={
                        "model": LOCAL_MODEL,
                        "prompt": full_prompt,
                        "stream": False
                    }
                )
                
                if ollama_resp.status_code == 200:
                    result = ollama_resp.json()
                    reply = result.get("response", "").strip() + route_str
                    return {
                        "reply": reply,
                        "result": reply,
                        "mode": "OFFLINE",
                        "model": LOCAL_MODEL
                    }
        except Exception:
            pass # Chuyển sang deterministic offline fallback nếu Ollama chưa mở
            
        # Fallback offline chuẩn không cần Ollama
        fallback_reply = (
            f"📱 **[COMPLETE AI - Chế độ Offline]**\n\n"
            f"Hiện hệ thống đang hoạt động ngoại tuyến. Thông tin tra cứu sẵn có:\n\n"
            f"{offline_context if offline_context else '- Vé buýt HN: 7.000đ-9.000đ/lượt | Metro 2A: 8.000đ-15.000đ/lượt'}"
            f"{route_str}"
        )
        return {
            "reply": fallback_reply,
            "result": fallback_reply,
            "mode": "OFFLINE_STATIC",
            "model": "offline-knowledge-base"
        }
                
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    print(f"Khoi dong Edge Gateway tai cong 8080...")
    print(f"Su dung Offline Model: {LOCAL_MODEL}")
    uvicorn.run("edge_gateway:app", host="0.0.0.0", port=8080, reload=True)
