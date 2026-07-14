"""
Route Planner Service - Smart Transport Graph Engine
"""
import networkx as nx
from typing import Dict, Any

# Mock Transit Graph Data (Expanded to 50+ nodes)
TRANSIT_NODES = {
    # HCM - Metro Line 1
    "BEN_THANH": {"name": "Bến Thành", "city": "HCM", "type": "metro_hub", "lat": 10.7716, "lng": 106.6967},
    "NHA_HAT_TP": {"name": "Nhà hát Thành phố", "city": "HCM", "type": "metro", "lat": 10.7766, "lng": 106.7032},
    "BA_SON": {"name": "Ba Son", "city": "HCM", "type": "metro", "lat": 10.7845, "lng": 106.7088},
    "VAN_THANH": {"name": "Công viên Văn Thánh", "city": "HCM", "type": "metro", "lat": 10.7963, "lng": 106.7180},
    "TAN_CANG": {"name": "Tân Cảng", "city": "HCM", "type": "metro", "lat": 10.7981, "lng": 106.7214},
    "THAO_DIEN": {"name": "Thảo Điền", "city": "HCM", "type": "metro", "lat": 10.8037, "lng": 106.7360},
    "AN_PHU": {"name": "An Phú", "city": "HCM", "type": "metro", "lat": 10.8030, "lng": 106.7441},
    "RACH_CHIEC": {"name": "Rạch Chiếc", "city": "HCM", "type": "metro", "lat": 10.8143, "lng": 106.7533},
    "PHUOC_LONG": {"name": "Phước Long", "city": "HCM", "type": "metro", "lat": 10.8228, "lng": 106.7645},
    "BINH_THAI": {"name": "Bình Thái", "city": "HCM", "type": "metro", "lat": 10.8322, "lng": 106.7699},
    "THU_DUC": {"name": "Thủ Đức", "city": "HCM", "type": "metro", "lat": 10.8496, "lng": 106.7749},
    "KCNC": {"name": "Khu Công nghệ cao", "city": "HCM", "type": "metro", "lat": 10.8569, "lng": 106.7869},
    "SUOI_TIEN": {"name": "Suối Tiên", "city": "HCM", "type": "metro", "lat": 10.8654, "lng": 106.8016},
    "BX_MIEN_DONG": {"name": "Bến xe Miền Đông mới", "city": "HCM", "type": "bus_hub", "lat": 10.8679, "lng": 106.8123},
    
    # HCM - Bus Hubs & Airports
    "SGN": {"name": "Sân bay Tân Sơn Nhất", "city": "HCM", "type": "airport", "lat": 10.8184, "lng": 106.6588},
    "CHO_LON": {"name": "Bến xe Chợ Lớn", "city": "HCM", "type": "bus_hub", "lat": 10.7508, "lng": 106.6521},
    "MIEN_TAY": {"name": "Bến xe Miền Tây", "city": "HCM", "type": "bus_hub", "lat": 10.7388, "lng": 106.6190},
    "AN_SUONG": {"name": "Bến xe An Sương", "city": "HCM", "type": "bus_hub", "lat": 10.8427, "lng": 106.6163},
    "DHQG_HCM": {"name": "Làng Đại Học QG", "city": "HCM", "type": "university", "lat": 10.8703, "lng": 106.7925},
    
    # HN - Metro Line 2A
    "CAT_LINH": {"name": "Cát Linh", "city": "HN", "type": "metro_hub", "lat": 21.0278, "lng": 105.8290},
    "LA_THANH": {"name": "La Thành", "city": "HN", "type": "metro", "lat": 21.0253, "lng": 105.8242},
    "THAI_HA": {"name": "Thái Hà", "city": "HN", "type": "metro", "lat": 21.0163, "lng": 105.8197},
    "LANG": {"name": "Láng", "city": "HN", "type": "metro", "lat": 21.0104, "lng": 105.8159},
    "KHTN": {"name": "ĐHKHTN - Nguyễn Trãi", "city": "HN", "type": "metro", "lat": 20.9939, "lng": 105.8080},
    "PHUNG_KHOANG": {"name": "Phùng Khoang", "city": "HN", "type": "metro", "lat": 20.9840, "lng": 105.7954},
    "HA_DONG": {"name": "Hà Đông", "city": "HN", "type": "metro", "lat": 20.9702, "lng": 105.7788},
    "YEN_NGHIA": {"name": "Yên Nghĩa", "city": "HN", "type": "metro_hub", "lat": 20.9497, "lng": 105.7483},
    
    # HN - Metro Line 3
    "NHON": {"name": "Nhổn", "city": "HN", "type": "metro_hub", "lat": 21.0544, "lng": 105.7348},
    "MINH_KHAI": {"name": "Minh Khai", "city": "HN", "type": "metro", "lat": 21.0494, "lng": 105.7454},
    "CAU_DIEN": {"name": "Cầu Diễn", "city": "HN", "type": "metro", "lat": 21.0371, "lng": 105.7645},
    "CAU_GIAY": {"name": "Cầu Giấy", "city": "HN", "type": "metro", "lat": 21.0286, "lng": 105.8016},
    "KIM_MA": {"name": "Kim Mã", "city": "HN", "type": "metro", "lat": 21.0309, "lng": 105.8236},
    "GA_HA_NOI": {"name": "Ga Hà Nội", "city": "HN", "type": "metro", "lat": 21.0245, "lng": 105.8412},
    
    # HN - Bus Hubs & Airports
    "HAN": {"name": "Sân bay Nội Bài", "city": "HN", "type": "airport", "lat": 21.2187, "lng": 105.8042},
    "MY_DINH": {"name": "Bến xe Mỹ Đình", "city": "HN", "type": "bus_hub", "lat": 21.0289, "lng": 105.7783},
    "GIAP_BAT": {"name": "Bến xe Giáp Bát", "city": "HN", "type": "bus_hub", "lat": 20.9808, "lng": 105.8414},
    "NUOC_NGAM": {"name": "Bến xe Nước Ngầm", "city": "HN", "type": "bus_hub", "lat": 20.9634, "lng": 105.8427},
}

TRANSIT_EDGES = [
    # HCM Metro Line 1 (Linear)
    ("BEN_THANH", "NHA_HAT_TP", "metro", "Metro 1", 2, 6000),
    ("NHA_HAT_TP", "BA_SON", "metro", "Metro 1", 2, 0),
    ("BA_SON", "VAN_THANH", "metro", "Metro 1", 3, 0),
    ("VAN_THANH", "TAN_CANG", "metro", "Metro 1", 2, 0),
    ("TAN_CANG", "THAO_DIEN", "metro", "Metro 1", 2, 0),
    ("THAO_DIEN", "AN_PHU", "metro", "Metro 1", 2, 0),
    ("AN_PHU", "RACH_CHIEC", "metro", "Metro 1", 3, 0),
    ("RACH_CHIEC", "PHUOC_LONG", "metro", "Metro 1", 2, 0),
    ("PHUOC_LONG", "BINH_THAI", "metro", "Metro 1", 2, 0),
    ("BINH_THAI", "THU_DUC", "metro", "Metro 1", 3, 0),
    ("THU_DUC", "KCNC", "metro", "Metro 1", 2, 0),
    ("KCNC", "SUOI_TIEN", "metro", "Metro 1", 2, 0),
    ("SUOI_TIEN", "BX_MIEN_DONG", "metro", "Metro 1", 2, 20000),
    
    # HCM Bus connections
    ("SGN", "BEN_THANH", "bus", "152", 35, 5000),
    ("CHO_LON", "BEN_THANH", "bus", "1", 20, 5000),
    ("MIEN_TAY", "CHO_LON", "bus", "14", 15, 6000),
    ("AN_SUONG", "BEN_THANH", "bus", "4", 45, 6000),
    ("BX_MIEN_DONG", "DHQG_HCM", "bus", "99", 10, 6000),
    ("TAN_CANG", "DHQG_HCM", "bus", "104", 30, 6000),
    
    # HN Metro Line 2A (Linear)
    ("CAT_LINH", "LA_THANH", "metro", "Metro 2A", 2, 8000),
    ("LA_THANH", "THAI_HA", "metro", "Metro 2A", 2, 0),
    ("THAI_HA", "LANG", "metro", "Metro 2A", 2, 0),
    ("LANG", "KHTN", "metro", "Metro 2A", 3, 0),
    ("KHTN", "PHUNG_KHOANG", "metro", "Metro 2A", 2, 0),
    ("PHUNG_KHOANG", "HA_DONG", "metro", "Metro 2A", 4, 0),
    ("HA_DONG", "YEN_NGHIA", "metro", "Metro 2A", 5, 15000),
    
    # HN Metro Line 3 (Linear)
    ("NHON", "MINH_KHAI", "metro", "Metro 3", 2, 8000),
    ("MINH_KHAI", "CAU_DIEN", "metro", "Metro 3", 2, 0),
    ("CAU_DIEN", "CAU_GIAY", "metro", "Metro 3", 6, 0),
    ("CAU_GIAY", "KIM_MA", "metro", "Metro 3", 3, 0),
    ("KIM_MA", "GA_HA_NOI", "metro", "Metro 3", 4, 12000),
    
    # HN Bus & BRT connections
    ("KIM_MA", "YEN_NGHIA", "brt", "BRT 01", 45, 7000),
    ("HAN", "KIM_MA", "bus", "90", 50, 9000),
    ("HAN", "CAU_GIAY", "bus", "109", 45, 8000),
    ("MY_DINH", "KIM_MA", "bus", "34", 25, 7000),
    ("GA_HA_NOI", "GIAP_BAT", "bus", "08", 20, 7000),
    ("GIAP_BAT", "NUOC_NGAM", "bus", "08", 10, 7000),
]

# Thêm edge ngược lại để đồ thị vô hướng (hoặc 2 chiều)
REVERSE_EDGES = []
for u, v, mode, line, time_mins, cost in TRANSIT_EDGES:
    REVERSE_EDGES.append((v, u, mode, line, time_mins, cost))
TRANSIT_EDGES.extend(REVERSE_EDGES)

def build_graph() -> nx.DiGraph:
    G = nx.DiGraph()
    for node_id, data in TRANSIT_NODES.items():
        G.add_node(node_id, **data)
        
    for u, v, mode, line, time_mins, cost in TRANSIT_EDGES:
        G.add_edge(u, v, mode=mode, line=line, weight=time_mins, cost=cost)
        
    return G

G = build_graph()

def find_route(start_query: str, end_query: str, city: str = None) -> Dict[str, Any]:
    """Find the fastest route between two locations using Dijkstra."""
    start_node = None
    end_node = None
    
    start_q_lower = start_query.lower()
    end_q_lower = end_query.lower()
    
    for node_id, data in G.nodes(data=True):
        if city and data.get("city") != city:
            continue
        name_lower = data["name"].lower()
        if not start_node and (start_q_lower in name_lower or name_lower in start_q_lower):
            start_node = node_id
        if not end_node and (end_q_lower in name_lower or name_lower in end_q_lower):
            end_node = node_id
            
    if not start_node or not end_node:
        return {"error": "Không tìm thấy điểm khởi hành hoặc điểm đến trong hệ thống dữ liệu."}
        
    try:
        path = nx.dijkstra_path(G, start_node, end_node, weight='weight')
        steps = []
        total_time = 0
        total_cost = 0
        
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i+1]
            edge_data = G[u][v]
            
            steps.append({
                "step": i + 1,
                "type": edge_data["mode"],
                "line": edge_data["line"],
                "from": G.nodes[u]["name"],
                "to": G.nodes[v]["name"],
                "from_lat": G.nodes[u]["lat"],
                "from_lng": G.nodes[u]["lng"],
                "to_lat": G.nodes[v]["lat"],
                "to_lng": G.nodes[v]["lng"],
                "duration": edge_data["weight"],
                "cost": edge_data["cost"]
            })
            total_time += edge_data["weight"]
            total_cost += edge_data["cost"]
            
        return {
            "origin": G.nodes[start_node]["name"],
            "origin_lat": G.nodes[start_node]["lat"],
            "origin_lng": G.nodes[start_node]["lng"],
            "destination": G.nodes[end_node]["name"],
            "dest_lat": G.nodes[end_node]["lat"],
            "dest_lng": G.nodes[end_node]["lng"],
            "steps": steps,
            "total_time": total_time,
            "total_cost": total_cost,
            "transfers": max(0, len(steps) - 1)
        }
        
    except nx.NetworkXNoPath:
        return {"error": f"Không tìm thấy lộ trình kết nối giữa {G.nodes[start_node]['name']} và {G.nodes[end_node]['name']}."}
