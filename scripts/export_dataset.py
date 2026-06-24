import sqlite3
import json
import os

DB_PATH = "completeai.db"
OUTPUT_FILE = "dataset.json"

def export_dataset():
    if not os.path.exists(DB_PATH):
        print(f"❌ Không tìm thấy database: {DB_PATH}")
        return

    # Kết nối SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Truy vấn lấy các câu trả lời tốt (feedback = 1)
    # Cấu trúc mong đợi từ bảng learning_events
    query = """
        SELECT question, answer 
        FROM learningevent 
        WHERE feedback = 1
    """
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"❌ Lỗi truy vấn: {e}")
        # Thử với tên bảng viết thường hoặc khác (tùy cấu trúc models.py)
        try:
            cursor.execute("SELECT question, answer FROM learning_event WHERE feedback = 1")
            rows = cursor.fetchall()
        except Exception as e2:
            print(f"❌ Vẫn lỗi: {e2}")
            return

    conn.close()

    if not rows:
        print("⚠️ Không tìm thấy dữ liệu có feedback = 1 (Tốt). Cần ít nhất vài chục câu để fine-tune.")
        # Lấy tạm các câu hỏi chưa có feedback để làm nháp nếu chưa có dữ liệu
        print("💡 Đang lấy tạm 100 câu hỏi gần nhất bất kể feedback để bạn làm quen quy trình...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT question, answer FROM learningevent LIMIT 100")
        rows = cursor.fetchall()
        conn.close()

    dataset = []
    for question, answer in rows:
        if not question or not answer: continue
        dataset.append({
            "instruction": "Bạn là CompleteAI, một trợ lý AI thông minh và chính xác. Hãy trả lời câu hỏi sau đây một cách chi tiết dựa trên kiến thức của bạn.",
            "input": question,
            "output": answer
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã xuất {len(dataset)} câu hỏi ra file: {OUTPUT_FILE}")
    print("👉 Hãy tải file dataset.json này lên Google Colab để tiến hành Fine-tune.")

if __name__ == "__main__":
    export_dataset()
