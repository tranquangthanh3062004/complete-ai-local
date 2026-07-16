"""
AI Topic Detection Service - Chuyên biệt về Giao Thông Công Cộng (GTCC)
"""

TOPIC_KEYWORDS = {
    "xe_buyt": [
        "xe buýt", "xe buyt", "bus", "tuyến buýt", "tuyen buyt", "bến xe",
        "trạm xe buýt", "tram xe buyt", "vé xe buýt", "ve xe buyt",
        "giờ xe buýt", "lịch xe buýt", "lich xe buyt", "số tuyến", "so tuyen",
        "xe bus", "minibus", "transerco", "ttqlgtcc",
    ],
    "metro_tau_dien": [
        "metro", "tàu điện", "tau dien", "đường sắt đô thị", "duong sat do thi",
        "mrt", "lrt", "tàu ngầm", "tau ngam", "ga metro", "cát linh",
        "cat linh", "hà đông", "ha dong", "nhổn", "nhon", "bến thành",
        "ben thanh", "suối tiên", "suoi tien", "tuyến metro", "tuyen metro",
        "tàu điện ngầm", "mrb", "vml",
    ],
    "brt_xe_buyt_nhanh": [
        "brt", "xe buýt nhanh", "xe buyt nhanh", "bus rapid transit",
        "kim mã", "kim ma", "yên nghĩa", "yen nghia", "làn đường riêng",
        "lan duong rieng",
    ],
    "ve_gia_cuoc": [
        "giá vé", "gia ve", "vé tháng", "ve thang", "vé ngày", "ve ngay",
        "học sinh sinh viên", "hoc sinh sinh vien", "miễn phí", "mien phi",
        "ưu đãi", "uu dai", "giảm giá", "giam gia", "thanh toán", "thanh toan",
        "mua vé", "mua ve", "thẻ xe buýt", "the xe buyt",
    ],
    "lich_trinh_tuyen": [
        "lịch trình", "lich trinh", "giờ chạy", "gio chay", "giờ mở cửa",
        "gio mo cua", "tần suất", "tan suat", "chuyến đầu", "chuyen dau",
        "chuyến cuối", "chuyen cuoi", "lộ trình", "lo trinh", "tuyến đường",
        "tuyen duong", "đón trả khách", "don tra khach",
    ],
    "luat_quy_dinh": [
        "luật", "luat", "quy định", "quy dinh", "nghị định", "nghi dinh",
        "vi phạm", "vi pham", "xử phạt", "xu phat", "phạt tiền", "phat tien",
        "đèn đỏ", "den do", "tốc độ", "toc do", "mũ bảo hiểm", "mu bao hiem",
        "nồng độ cồn", "nong do con", "bằng lái", "bang lai", "giấy phép",
        "giay phep", "luật giao thông", "luat giao thong",
    ],
    "giao_thong_duong_thuy": [
        "buýt sông", "buyt song", "phà", "pha", "tàu thủy", "tau thuy",
        "đường thủy", "duong thuy", "bến phà", "ben pha", "sông sài gòn",
        "song sai gon", "cần giờ", "can gio",
    ],
    "ung_dung_tien_ich": [
        "busmap", "imaas", "ứng dụng", "ung dung", "app", "google maps",
        "tra cứu", "tra cuu", "thông tin tuyến", "thong tin tuyen",
        "thẻ thông minh", "the thong minh", "thanh toán điện tử",
        "thanh toan dien tu", "qr code", "mã qr",
    ],
    "xe_dap_xe_may_chia_se": [
        "xe đạp chia sẻ", "xe dap chia se", "xe máy điện chia sẻ",
        "xe may dien chia se", "tnego", "ecobike", "mobike", "grab bike",
        "xe điện", "xe dien",
    ],
    "san_bay_ga_tau": [
        "sân bay", "san bay", "tân sơn nhất", "tan son nhat", "nội bài",
        "noi bai", "ga tàu", "ga tau", "từ sân bay", "tu san bay",
        "đến trung tâm", "den trung tam",
    ],
}

def detect_topic(text: str) -> str:
    text_lower = text.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return topic
    return "gtcc_chung"

# Tên hiển thị topic đẹp hơn
TOPIC_DISPLAY = {
    "xe_buyt": "🚌 Xe Buýt",
    "metro_tau_dien": "🚇 Metro / Tàu Điện",
    "brt_xe_buyt_nhanh": "🚍 BRT - Xe Buýt Nhanh",
    "ve_gia_cuoc": "🎫 Vé & Giá Cước",
    "lich_trinh_tuyen": "🗓️ Lịch Trình / Tuyến",
    "luat_quy_dinh": "📋 Luật & Quy Định",
    "giao_thong_duong_thuy": "⛵ Giao Thông Đường Thủy",
    "ung_dung_tien_ich": "📱 Ứng Dụng & Tiện Ích",
    "xe_dap_xe_may_chia_se": "🛵 Xe Đạp / Xe Máy Chia Sẻ",
    "san_bay_ga_tau": "✈️ Sân Bay & Nhà Ga",
    "gtcc_chung": "🚦 GTCC Chung",
}

def _get_gtcc_suggestions(topic: str) -> list:
    """Gợi ý câu hỏi tiếp theo theo chủ đề GTCC."""
    suggestions_map = {
        "xe_buyt": [
            "Giá vé xe buýt Hà Nội là bao nhiêu?",
            "Làm sao làm vé tháng xe buýt Hà Nội?",
            "Tuyến xe buýt nào đi qua Hồ Gươm?",
        ],
        "metro_tau_dien": [
            "Giờ chạy của metro Cát Linh - Hà Đông?",
            "Giá vé metro Nhổn - Ga Hà Nội?",
            "Mua vé tháng metro Hà Nội ở đâu?",
        ],
        "ve_gia_cuoc": [
            "Sinh viên được giảm giá vé buýt Hà Nội không?",
            "Làm vé tháng xe buýt liên tuyến hết bao nhiêu?",
            "Người cao tuổi đi xe buýt có mất tiền không?",
        ],
        "luat_quy_dinh": [
            "Lỗi đi vào làn BRT bị phạt bao nhiêu?",
            "Không đội mũ bảo hiểm phạt bao nhiêu?",
            "Chạy quá tốc độ trong phố bị phạt thế nào?",
        ],
        "san_bay_ga_tau": [
            "Đi từ sân bay Nội Bài vào trung tâm bằng xe buýt nào?",
            "Xe buýt 86 đi từ Ga Hà Nội ra Nội Bài giá bao nhiêu?",
            "Lịch trình xe buýt 68 từ Cầu Giấy đi Nội Bài?",
        ],
    }
    default = [
        "Làm sao đi xe buýt từ Mỹ Đình lên Hồ Gươm?",
        "Tuyến xe buýt BRT 01 chạy đường nào?",
        "App nào tra cứu xe buýt Hà Nội chuẩn nhất?",
    ]
    return suggestions_map.get(topic, default)
