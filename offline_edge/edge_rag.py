import os
import chromadb

# Thư mục lưu trữ CSDL Vector cục bộ
DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")

# Khởi tạo ChromaDB client
client = chromadb.PersistentClient(path=DB_DIR)

# Lấy hoặc tạo collection (sử dụng model embedding mặc định all-MiniLM-L6-v2 cực nhẹ qua ONNX)
collection = client.get_or_create_collection(name="gtcc_offline_knowledge")

def init_offline_knowledge():
    """Tải tri thức GTCC mở rộng vào CSDL Vector cục bộ để dùng offline."""
    if collection.count() > 0:
        return
        
    documents = [
        # Vé & Giá cước
        "Vé xe buýt Hà Nội thông thường có giá từ 7.000 VNĐ đến 9.000 VNĐ một lượt tùy cự ly tuyến.",
        "Vé tháng xe buýt Hà Nội: Tuyến đơn 100.000 VNĐ/tháng, Liên tuyến 200.000 VNĐ/tháng. Học sinh, sinh viên, công nhân KCN được giảm 50% (Đơn tuyến 50.000 VNĐ, Liên tuyến 100.000 VNĐ).",
        "Người cao tuổi (từ 60 tuổi trở lên), người có công, người khuyết tật, và trẻ em dưới 6 tuổi được miễn phí toàn bộ vé xe buýt và Metro tại Hà Nội.",
        "Tuyến Metro Cát Linh - Hà Đông (Tuyến 2A): Giá vé chặng từ 8.000 VNĐ đến 15.000 VNĐ/lượt. Vé ngày 30.000 VNĐ (đi không giới hạn). Vé tháng phổ thông 200.000 VNĐ, sinh viên 100.000 VNĐ.",
        "Tuyến Metro Nhổn - Ga Hà Nội (Đoạn trên cao Nhổn - Cầu Giấy): Có 8 ga (Nhổn, Minh Khai, Phú Diễn, Cầu Diễn, Lê Đức Thọ, Đại học Quốc gia, Chùa Hà, Cầu Giấy). Giá vé lượt từ 8.000 VNĐ đến 12.000 VNĐ.",
        
        # Tuyến Sân bay & Xe buýt chính
        "Tuyến xe buýt chất lượng cao 86: Đi từ Ga Hà Nội - Hồ Hoàn Kiếm - Sân bay Nội Bài, giá vé 45.000 VNĐ/lượt, thời gian di chuyển ~45-55 phút.",
        "Tuyến xe buýt chất lượng cao 68: Đi từ Trung tâm Thương mại Mê Linh Plaza Hà Đông - Sân bay Nội Bài, giá vé 50.000 VNĐ/lượt.",
        "Tuyến xe buýt 07: Bến xe Cầu Giấy - Sân bay Nội Bài, giá vé 9.000 VNĐ/lượt.",
        "Tuyến xe buýt 17: Bến xe Long Biên - Sân bay Nội Bài, giá vé 9.000 VNĐ/lượt.",
        "Tuyến xe buýt 01: Bến xe Gia Lâm - Bến xe Yên Nghĩa (đi qua Long Biên, Trần Hưng Đạo, Nguyễn Trãi), giá 7.000 VNĐ.",
        "Tuyến xe buýt 02: Bến xe Bác Cổ - Bến xe Yên Nghĩa (đi qua Tràng Thi, Điện Biên Phủ, Trần Phú, Nguyễn Trãi), giá 7.000 VNĐ.",
        "Tuyến xe buýt điện VinBus E01: Bến xe Mỹ Đình - Khu đô thị Ocean Park.",
        
        # Phương tiện xanh & Xe đạp công cộng
        "Dịch vụ xe đạp công cộng TNGO: Giá thuê 5.000 VNĐ cho 30 phút đối với xe đạp thường, 10.000 VNĐ cho 30 phút đối với xe đạp điện. Mua qua ứng dụng TNGO.",
        "Các điểm trạm xe đạp TNGO tập trung tại các ga Metro Cát Linh - Hà Đông, trạm xe buýt lớn và khu vực Hồ Hoàn Kiếm.",
        
        # Quy định & Luật Giao thông
        "Mức phạt vi phạm giao thông (Nghị định 100/2019/NĐ-CP & 123/2021/NĐ-CP): Không đội mũ bảo hiểm bị phạt từ 400.000đ đến 600.000đ. Vượt đèn đỏ xe máy phạt 1.000.000đ - 2.000.000đ, ô tô phạt 4.000.000đ - 6.000.000đ. Nồng độ cồn xe máy cao nhất phạt 6.000.000đ - 8.000.000đ và tước GPLX 22-24 tháng.",
    ]
    
    ids = [f"doc_{i}" for i in range(len(documents))]
    collection.add(documents=documents, ids=ids)
    print(f"✅ Đã tải {len(documents)} tài liệu chuẩn vào Offline Knowledge Base.")

def search_offline_knowledge(query: str, n_results: int = 3) -> str:
    """Tìm kiếm tài liệu liên quan trong CSDL Vector cục bộ."""
    if collection.count() == 0:
        return ""
        
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    if not results or not results['documents'] or not results['documents'][0]:
        return ""
        
    distances = results.get('distances', [[0]*n_results])[0]
    docs = results.get('documents', [[]])[0]
    
    valid_docs = []
    # Dùng ngưỡng L2 distance linh hoạt hơn (<= 1.45 cho MiniLM)
    THRESHOLD = 1.45 
    for doc, dist in zip(docs, distances):
        if dist <= THRESHOLD:
            valid_docs.append(f"- {doc}")
            
    if not valid_docs:
        # Trả về kết quả tốt nhất nếu câu hỏi quá ngắn
        return f"- {docs[0]}" if docs else ""
        
    return "\n".join(valid_docs)

# Tự động khởi tạo dữ liệu khi module được import
init_offline_knowledge()
