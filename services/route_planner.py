"""
Route Planner Service - Smart Transport Graph Engine
"""
import networkx as nx
from typing import Dict, Any, List
import httpx
import math

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

import math
import re
import httpx

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def geocode_address(query: str):
    if not query or not query.strip():
        return None
        
    query = query.strip()
    
    # 1. Direct regex match for lat,lng coordinates (e.g. "21.0285,105.8542")
    coords_match = re.match(r"^\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*$", query)
    if coords_match:
        try:
            lat = float(coords_match.group(1))
            lng = float(coords_match.group(2))
            return {
                "name": f"Vị trí GPS ({lat:.4f}, {lng:.4f})",
                "lat": lat,
                "lng": lng
            }
        except ValueError:
            pass

    # 2. OpenStreetMap Nominatim Geocoding (Hanoi Priority)
    url = "https://nominatim.openstreetmap.org/search"
    search_q = query if "hà nội" in query.lower() or "hanoi" in query.lower() else f"{query}, Hà Nội, Việt Nam"
    
    headers = {"User-Agent": "GTCC-Bot-App/3.0"}
    try:
        response = httpx.get(url, params={"q": search_q, "format": "json", "countrycodes": "vn", "limit": 1}, headers=headers, timeout=5.0)
        data = response.json() if response.status_code == 200 else []
        
        if not data and search_q != query:
            response = httpx.get(url, params={"q": query, "format": "json", "countrycodes": "vn", "limit": 1}, headers=headers, timeout=5.0)
            data = response.json() if response.status_code == 200 else []

        if data and len(data) > 0:
            return {
                "name": data[0].get("display_name"),
                "lat": float(data[0].get("lat")),
                "lng": float(data[0].get("lon"))
            }
    except Exception:
        pass
    return None

def fetch_osrm_geometry(lat1: float, lon1: float, lat2: float, lon2: float) -> List[List[float]]:
    """Fetch detailed road geometry from OSRM for real road polylines."""
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        res = httpx.get(url, timeout=3.0)
        if res.status_code == 200:
            data = res.json()
            if data.get("routes") and len(data["routes"]) > 0:
                coords = data["routes"][0]["geometry"]["coordinates"]
                return [[c[1], c[0]] for c in coords]
    except Exception:
        pass
    return [[lat1, lon1], [lat2, lon2]]

def find_nearest_node(lat, lng, city=None):
    best_node = None
    min_dist = float('inf')
    for node_id, data in G.nodes(data=True):
        if city and data.get("city") != city:
            continue
        dist = haversine(lat, lng, data["lat"], data["lng"])
        if dist < min_dist:
            min_dist = dist
            best_node = node_id
    return best_node, min_dist

def find_route(start_query: str, end_query: str, city: str = None) -> Dict[str, Any]:
    """Find the fastest route between two locations using Dijkstra with Geocoding Fallback."""
    start_node = None
    end_node = None
    
    start_q_lower = start_query.lower()
    end_q_lower = end_query.lower()
    
    # 1. Exact or Substring match
    for node_id, data in G.nodes(data=True):
        if city and data.get("city") != city:
            continue
        name_lower = data["name"].lower()
        if not start_node and (start_q_lower in name_lower or name_lower in start_q_lower):
            start_node = node_id
        if not end_node and (end_q_lower in name_lower or name_lower in end_q_lower):
            end_node = node_id
            
    # 2. Geocoding Fallback
    start_geo = None
    end_geo = None
    
    if not start_node:
        start_geo = geocode_address(start_query)
        if start_geo:
            start_node, _ = find_nearest_node(start_geo["lat"], start_geo["lng"], city)
            
    if not end_node:
        end_geo = geocode_address(end_query)
        if end_geo:
            end_node, _ = find_nearest_node(end_geo["lat"], end_geo["lng"], city)
            
    if not start_node or not end_node:
        return {"error": "Không tìm thấy điểm khởi hành hoặc điểm đến trong hệ thống dữ liệu. Vui lòng nhập địa chỉ cụ thể hơn."}
        
    try:
        path = nx.dijkstra_path(G, start_node, end_node, weight='weight')
        steps = []
        total_time = 0
        total_cost = 0
        
        # Add walking step from Origin to start_node if geocoded
        if start_geo and start_node:
            s_lat, s_lng = G.nodes[start_node]["lat"], G.nodes[start_node]["lng"]
            dist_km = haversine(start_geo["lat"], start_geo["lng"], s_lat, s_lng)
            duration_mins = int(dist_km / 5.0 * 60) # 5 km/h walking speed
            if duration_mins > 0:
                steps.append({
                    "step": 0,
                    "type": "walk",
                    "line": "Đi bộ",
                    "from": start_geo["name"].split(',')[0],
                    "to": G.nodes[start_node]["name"],
                    "from_lat": start_geo["lat"],
                    "from_lng": start_geo["lng"],
                    "to_lat": s_lat,
                    "to_lng": s_lng,
                    "duration": duration_mins,
                    "cost": 0
                })
                total_time += duration_mins
            
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i+1]
            edge_data = G[u][v]
            
            u_lat, u_lng = G.nodes[u]["lat"], G.nodes[u]["lng"]
            v_lat, v_lng = G.nodes[v]["lat"], G.nodes[v]["lng"]
            poly = fetch_osrm_geometry(u_lat, u_lng, v_lat, v_lng)
            
            steps.append({
                "step": len(steps) + 1,
                "type": edge_data["mode"],
                "line": edge_data["line"],
                "from": G.nodes[u]["name"],
                "to": G.nodes[v]["name"],
                "from_lat": u_lat,
                "from_lng": u_lng,
                "to_lat": v_lat,
                "to_lng": v_lng,
                "polyline_coords": poly,
                "duration": edge_data["weight"],
                "cost": edge_data["cost"]
            })
            total_time += edge_data["weight"]
            total_cost += edge_data["cost"]
            
        # Add walking step from end_node to Destination if geocoded
        if end_geo and end_node:
            e_lat, e_lng = G.nodes[end_node]["lat"], G.nodes[end_node]["lng"]
            dist_km = haversine(end_geo["lat"], end_geo["lng"], e_lat, e_lng)
            duration_mins = int(dist_km / 5.0 * 60)
            if duration_mins > 0:
                steps.append({
                    "step": len(steps) + 1,
                    "type": "walk",
                    "line": "Đi bộ",
                    "from": G.nodes[end_node]["name"],
                    "to": end_geo["name"].split(',')[0],
                    "from_lat": e_lat,
                    "from_lng": e_lng,
                    "to_lat": end_geo["lat"],
                    "to_lng": end_geo["lng"],
                    "duration": duration_mins,
                    "cost": 0
                })
                total_time += duration_mins
            
        origin_name = start_geo["name"].split(',')[0] if start_geo else G.nodes[start_node]["name"]
        origin_lat = start_geo["lat"] if start_geo else G.nodes[start_node]["lat"]
        origin_lng = start_geo["lng"] if start_geo else G.nodes[start_node]["lng"]
        
        dest_name = end_geo["name"].split(',')[0] if end_geo else G.nodes[end_node]["name"]
        dest_lat = end_geo["lat"] if end_geo else G.nodes[end_node]["lat"]
        dest_lng = end_geo["lng"] if end_geo else G.nodes[end_node]["lng"]
            
        return {
            "origin": origin_name,
            "origin_lat": origin_lat,
            "origin_lng": origin_lng,
            "destination": dest_name,
            "dest_lat": dest_lat,
            "dest_lng": dest_lng,
            "steps": steps,
            "total_time": total_time,
            "total_cost": total_cost,
            "transfers": max(0, len(path) - 1)
        }
        
    except nx.NetworkXNoPath:
        return {"error": f"Không tìm thấy lộ trình kết nối giữa {G.nodes[start_node]['name']} và {G.nodes[end_node]['name']}."}
