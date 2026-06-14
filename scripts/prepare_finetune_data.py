import os
import json
import re

DATA_DIR = r"c:\Users\ADMIN 88\OneDrive\Desktop\my_open_llm\data"
HANOI_DIR = os.path.join(DATA_DIR, "hanoi")
OUT_FILE = os.path.join(DATA_DIR, "finetune_gtcc.jsonl")

SYSTEM_PROMPT = "Bạn là trợ lý ảo AI thông minh chuyên về Giao thông công cộng tại Việt Nam (xe buýt, metro). Hãy trả lời chính xác, ngắn gọn và hữu ích."

def create_chatml_record(user_msg, assistant_msg):
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": assistant_msg}
        ]
    }

def generate_bus_qa():
    records = []
    file_path = os.path.join(HANOI_DIR, "buyt_online_hanoi.txt")
    if not os.path.exists(file_path):
        return records
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Tìm các block Tuyến buýt
    # Ví dụ: ### Tuyến 09A: Bờ Hồ (hoặc Trần Khánh Dư) ⇄ Đại học Mỏ\n* Lộ trình...
    blocks = re.split(r'###\s+', content)
    for block in blocks[1:]:
        lines = block.strip().split('\n')
        if not lines: continue
        
        tuyen_name = lines[0].strip() # "Tuyến 09A: Bờ Hồ (hoặc Trần Khánh Dư) ⇄ Đại học Mỏ"
        m = re.match(r'(Tuyến\s+\w+):(.*)', tuyen_name)
        if m:
            tuyen_id = m.group(1).strip()
            details = "\n".join([l.strip() for l in lines[1:] if l.strip()])
            
            # Tạo nhiều biến thể câu hỏi
            q1 = f"Lộ trình {tuyen_id} ở Hà Nội như thế nào?"
            a1 = f"{tuyen_name}.\nChi tiết:\n{details}"
            records.append(create_chatml_record(q1, a1))
            
            q2 = f"Cho mình hỏi thông tin {tuyen_id} đi qua những đâu?"
            records.append(create_chatml_record(q2, a1))
            
            q3 = f"Xe {tuyen_id.lower()} đi từ đâu đến đâu?"
            records.append(create_chatml_record(q3, a1))
            
    return records

def generate_metro_qa():
    records = []
    file_path = os.path.join(HANOI_DIR, "metro_hanoi.txt")
    if not os.path.exists(file_path):
        return records
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Extract Tuyến 2A info
    if "B1. TUYẾN 2A: CÁT LINH – HÀ ĐÔNG" in content:
        q1 = "Tuyến metro Cát Linh Hà Đông có bao nhiêu ga và lộ trình như thế nào?"
        a1 = """Tuyến metro 2A (Cát Linh - Hà Đông) có chiều dài 13km với 12 ga trên cao. 
Lộ trình 12 ga gồm: 
Ga 01 - Cát Linh
Ga 02 - La Thành
Ga 03 - Thái Hà
Ga 04 - Láng
Ga 05 - Thượng Đình
Ga 06 - Vành Đai 3
Ga 07 - Phùng Khoang
Ga 08 - Văn Quán
Ga 09 - Hà Đông
Ga 10 - La Khê
Ga 11 - Văn Khê
Ga 12 - Yên Nghĩa."""
        records.append(create_chatml_record(q1, a1))
        
        q2 = "Giá vé metro Cát Linh Hà Đông là bao nhiêu?"
        a2 = """Giá vé tuyến metro Cát Linh - Hà Đông như sau:
- Đi 1-4 ga: 8.000 đồng
- Đi 5-8 ga: 10.000 đồng
- Đi 9-12 ga (toàn tuyến): 15.000 đồng
- Vé ngày (không giới hạn lượt đi): 30.000 đồng
- Vé tháng thường: 200.000 đồng
- Vé tháng sinh viên: 100.000 đồng
Trẻ em dưới 6 tuổi, người trên 60 tuổi và người khuyết tật được miễn phí vé."""
        records.append(create_chatml_record(q2, a2))

        q3 = "Metro Cát Linh Hà Đông hoạt động đến mấy giờ?"
        a3 = "Tuyến metro 2A Cát Linh - Hà Đông hoạt động từ 05:30 sáng đến 22:30 tối hàng ngày. Tần suất chuyến vào giờ cao điểm là 6 phút/chuyến, giờ bình thường là 10 phút/chuyến."
        records.append(create_chatml_record(q3, a3))

    if "TUYẾN 3: NHỔN – GA HÀ NỘI" in content:
        q1 = "Tuyến Nhổn - ga Hà Nội đã chạy chưa?"
        a1 = "Đoạn trên cao của tuyến metro Nhổn - ga Hà Nội (từ ga Nhổn đến ga Cầu Giấy, gồm 8 ga trên cao) đã chính thức vận hành thương mại từ ngày 08/08/2024. Đoạn ngầm (4 ga) dự kiến sẽ hoàn thành vào cuối năm 2027."
        records.append(create_chatml_record(q1, a1))
        
    return records

def generate_general_qa():
    records = []
    # Thêm một số Q&A tự nhiên phổ biến
    qa_pairs = [
        ("Nghị định 100/2019 là gì?", "Nghị định 100/2019/NĐ-CP là nghị định của Chính phủ Việt Nam quy định xử phạt vi phạm hành chính trong lĩnh vực giao thông đường bộ và đường sắt. Nghị định này nổi bật với quy định tăng mức phạt nặng đối với hành vi sử dụng rượu bia khi tham gia giao thông."),
        ("Làm sao để tìm trạm xe buýt gần nhất?", "Bạn có thể sử dụng các ứng dụng như BusMap, Tìm Buýt (Hà Nội) hoặc Google Maps. Chỉ cần bật định vị GPS, ứng dụng sẽ hiển thị các trạm xe buýt gần vị trí của bạn cùng với thời gian xe tới (ETA)."),
        ("Mang thú cưng lên xe buýt được không?", "Theo quy định, xe buýt công cộng không cho phép mang theo động vật sống (bao gồm cả thú cưng như chó, mèo) lên xe để đảm bảo an toàn và vệ sinh cho các hành khách khác."),
        ("Xe BRT là gì?", "BRT (Bus Rapid Transit) là hệ thống xe buýt nhanh. Ở Hà Nội, xe BRT chạy trên làn đường dành riêng, có thiết kế trạm đỗ hiện đại ngang mức sàn xe, giúp xe di chuyển nhanh và an toàn hơn xe buýt thường.")
    ]
    for q, a in qa_pairs:
        records.append(create_chatml_record(q, a))
        
    return records

def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("Dang tao tap du lieu Fine-tuning...")
    all_records = []
    all_records.extend(generate_bus_qa())
    all_records.extend(generate_metro_qa())
    all_records.extend(generate_general_qa())
    
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
    print(f"Da tao thanh cong {len(all_records)} ban ghi fine-tuning tai: {OUT_FILE}")

if __name__ == "__main__":
    main()
