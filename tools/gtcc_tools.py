"""
Tập hợp các LangChain Tools (Công cụ) cho GTCC Bot.
Được viết với Prompt tối ưu nhất (Docstrings) để AI (như Llama 3 / Groq / Gemini) có thể tự động gọi (Function Calling).
"""

from langchain.tools import tool
from typing import Optional

@tool
def search_bus_route(route_number_or_name: str, city: str = "TP.HCM") -> str:
    """
    Tìm kiếm thông tin chi tiết về một tuyến xe buýt cụ thể (Lộ trình, giá vé, thời gian chạy).
    Luôn gọi công cụ này khi người dùng hỏi về:
    - "Xe buýt số 150 đi đường nào?"
    - "Lộ trình tuyến 86 Hà Nội"
    
    Args:
        route_number_or_name (str): Tên hoặc số hiệu tuyến xe buýt (vd: "150", "08", "86").
        city (str): Thành phố (mặc định là "TP.HCM", có thể truyền "Hà Nội").
        
    Returns:
        str: Chuỗi thông tin chi tiết về tuyến xe buýt.
    """
    # TODO: Kết nối với Database thật hoặc file CSV. Dưới đây là Mock Data.
    if "150" in route_number_or_name:
        return "Tuyến 150: Bến xe Chợ Lớn - Ngã 3 Tân Vạn. Thời gian hoạt động: 04:30 - 21:00. Giá vé: 6.000đ/lượt. Lộ trình chính: Châu Văn Liêm, Thuận Kiều, Hồng Bàng, Kinh Dương Vương, Xa Lộ Hà Nội."
    elif "86" in route_number_or_name and "Hà Nội" in city:
        return "Tuyến 86: Ga Hà Nội - Sân bay Nội Bài. Thời gian hoạt động: 05:05 - 21:40. Giá vé: 35.000đ/lượt. Đây là tuyến xe buýt chất lượng cao không trợ giá."
    
    return f"Hệ thống tạm thời chưa có dữ liệu chi tiết cho tuyến {route_number_or_name} tại {city}."

@tool
def get_ticket_price(transport_type: str, passenger_type: str = "normal") -> str:
    """
    Tra cứu giá vé cho các loại hình giao thông công cộng (Xe buýt, Metro, Tàu điện).
    Gọi công cụ này khi người dùng hỏi:
    - "Vé xe buýt sinh viên bao nhiêu tiền?"
    - "Giá vé metro Bến Thành Suối Tiên"
    
    Args:
        transport_type (str): Loại hình (vd: "bus_hcm", "bus_hn", "metro_hcm", "metro_hn").
        passenger_type (str): Đối tượng hành khách ("normal", "student", "elderly").
        
    Returns:
        str: Thông tin chính xác về giá vé.
    """
    if "metro_hcm" in transport_type:
        if passenger_type == "student":
            return "Metro HCM số 1 (Bến Thành - Suối Tiên) có giá vé tháng ưu đãi cho HSSV là 150.000đ."
        return "Metro HCM số 1 (Bến Thành - Suối Tiên): Giá vé lượt từ 6.000đ - 20.000đ tùy khoảng cách. Vé tháng: 300.000đ."
    
    if "bus" in transport_type:
        if passenger_type == "student":
            return "Vé xe buýt trợ giá cho Sinh viên/Học sinh: 3.000đ/lượt (yêu cầu xuất trình thẻ HSSV)."
        return "Vé xe buýt trợ giá thông thường: 5.000đ - 7.000đ/lượt tùy tuyến."
    
    return "Miễn phí vé cho người cao tuổi (trên 70 tuổi), trẻ em cao dưới 1.3m, và người khuyết tật."

@tool
def check_penalty_law(violation: str) -> str:
    """
    Tra cứu mức xử phạt vi phạm giao thông dựa theo Nghị định 100/2019/NĐ-CP và NĐ 123/2021/NĐ-CP.
    Gọi công cụ này khi người dùng hỏi:
    - "Vượt đèn đỏ phạt bao nhiêu?"
    - "Đi xe máy không đội mũ bảo hiểm"
    
    Args:
        violation (str): Hành vi vi phạm cần tra cứu (vd: "vượt đèn đỏ", "nồng độ cồn").
        
    Returns:
        str: Mức phạt cụ thể theo quy định pháp luật hiện hành.
    """
    violation = violation.lower()
    if "đèn đỏ" in violation:
        return "Vượt đèn đỏ: Phạt 4.000.000 - 6.000.000 VNĐ đối với Ô tô (tước bằng 1-3 tháng). Phạt 800.000 - 1.000.000 VNĐ đối với Xe máy (tước bằng 1-3 tháng)."
    if "cồn" in violation:
        return "Vi phạm nồng độ cồn: Tối đa 30-40 triệu đồng đối với Ô tô (tước bằng 22-24 tháng). Tối đa 6-8 triệu đồng đối với Xe máy (tước bằng 22-24 tháng)."
    if "mũ bảo hiểm" in violation:
        return "Không đội mũ bảo hiểm: Phạt tiền từ 400.000 - 600.000 VNĐ (áp dụng cho người điều khiển và người ngồi trên xe mô tô, xe gắn máy)."
    
    return "Hành vi vi phạm này cần tham khảo chi tiết tại Nghị định 100/2019/NĐ-CP và 123/2021/NĐ-CP."

# Danh sách các công cụ để Inject vào LLM Agent
GTCC_AGENT_TOOLS = [search_bus_route, get_ticket_price, check_penalty_law]
