import networkx as nx
from typing import Dict, Any, List
from services.route_planner import G, haversine, geocode_address, find_nearest_node, fetch_osrm_geometry

def find_multiple_routes(start_query: str, end_query: str, city: str = None) -> List[Dict[str, Any]]:
    """Tìm nhiều lộ trình với các tiêu chí khác nhau (Nhanh nhất, Rẻ nhất, Ít chuyển tuyến)."""
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
        return build_osrm_fallback_options(start_query, end_query, start_geo, end_geo)
        
    try:
        # Lấy 3 đường đi ngắn nhất (ít node nhất hoặc thời gian gần nhau)
        paths = list(nx.shortest_simple_paths(G, start_node, end_node, weight='weight'))[:3]
        options = []
        
        for idx, path in enumerate(paths):
            steps = []
            total_time = 0
            total_cost = 0
            
            for i in range(len(path) - 1):
                u = path[i]
                v = path[i+1]
                edge_data = G[u][v]
                
                u_lat, u_lng = G.nodes[u]["lat"], G.nodes[u]["lng"]
                v_lat, v_lng = G.nodes[v]["lat"], G.nodes[v]["lng"]
                try:
                    poly = fetch_osrm_geometry(u_lat, u_lng, v_lat, v_lng)
                except Exception:
                    poly = [[u_lat, u_lng], [v_lat, v_lng]]
                
                steps.append({
                    "mode": edge_data["mode"],
                    "type": edge_data["mode"],
                    "line": edge_data["line"],
                    "from": G.nodes[u]["name"],
                    "to": G.nodes[v]["name"],
                    "from_lat": u_lat,
                    "from_lng": u_lng,
                    "to_lat": v_lat,
                    "to_lng": v_lng,
                    "polyline_coords": poly,
                    "duration": edge_data["weight"]
                })
                total_time += edge_data["weight"]
                total_cost += edge_data["cost"]
                
            transfers = max(0, len(path) - 1)
            walk_distance = 0
            
            if start_geo:
                s_lat, s_lng = G.nodes[start_node]["lat"], G.nodes[start_node]["lng"]
                dist = haversine(start_geo["lat"], start_geo["lng"], s_lat, s_lng)
                walk_distance += dist
                total_time += int(dist / 5.0 * 60)
            if end_geo:
                e_lat, e_lng = G.nodes[end_node]["lat"], G.nodes[end_node]["lng"]
                dist = haversine(end_geo["lat"], end_geo["lng"], e_lat, e_lng)
                walk_distance += dist
                total_time += int(dist / 5.0 * 60)
                
            co2 = round((total_time * 0.2) if "bus" in [s["mode"] for s in steps] else (total_time * 0.05), 2)
            
            option_name = "Nhanh nhất" if idx == 0 else ("Rẻ nhất" if total_cost == 0 else "Ít chuyển tuyến")
            if idx == 2: option_name = "Xanh nhất (Xe đạp TNGO / Đi bộ)"
            
            options.append({
                "option_name": option_name,
                "origin": start_query.title(),
                "destination": end_query.title(),
                "origin_lat": start_geo["lat"] if start_geo else G.nodes[start_node]["lat"],
                "origin_lng": start_geo["lng"] if start_geo else G.nodes[start_node]["lng"],
                "dest_lat": end_geo["lat"] if end_geo else G.nodes[end_node]["lat"],
                "dest_lng": end_geo["lng"] if end_geo else G.nodes[end_node]["lng"],
                "total_time": total_time,
                "total_cost": total_cost,
                "transfers": transfers,
                "walk_km": round(walk_distance, 2),
                "co2_kg": co2,
                "steps": steps
            })
            
        return options
        
    except Exception:
        return build_osrm_fallback_options(start_query, end_query, start_geo, end_geo)

def build_osrm_fallback_options(start_query: str, end_query: str, start_geo: dict = None, end_geo: dict = None) -> List[Dict[str, Any]]:
    if not start_geo:
        start_geo = geocode_address(start_query)
    if not end_geo:
        end_geo = geocode_address(end_query)
        
    if not start_geo or not end_geo:
        return []
        
    lat1, lon1 = start_geo["lat"], start_geo["lng"]
    lat2, lon2 = end_geo["lat"], end_geo["lng"]
    
    dist_km = round(haversine(lat1, lon1, lat2, lon2), 1)
    dur_mins = max(5, int(dist_km / 20.0 * 60))
    poly = fetch_osrm_geometry(lat1, lon1, lat2, lon2)
    
    start_name = start_geo.get("name", start_query).split(',')[0]
    end_name = end_geo.get("name", end_query).split(',')[0]
    
    suggested_line = "Xe buýt 01 / 02 / 21A / 26 / 31"
    s_low = start_query.lower()
    e_low = end_query.lower()
    if "nội bài" in s_low or "nội bài" in e_low:
        suggested_line = "Xe buýt 86 / 68 / 07 / 90"
    elif "cát linh" in s_low or "hà đông" in s_low:
        suggested_line = "Metro 2A (Cát Linh - Hà Đông) kết hợp Xe buýt"

    step_bus = {
        "step": 1,
        "mode": "bus",
        "type": "bus",
        "line": suggested_line,
        "from": start_name,
        "to": end_name,
        "from_lat": lat1,
        "from_lng": lon1,
        "to_lat": lat2,
        "to_lng": lon2,
        "polyline_coords": poly,
        "duration": dur_mins,
        "cost": 7000
    }
    
    step_eco = {
        "step": 1,
        "mode": "bike",
        "type": "bike",
        "line": "Xe đạp TNGO",
        "from": start_name,
        "to": end_name,
        "from_lat": lat1,
        "from_lng": lon1,
        "to_lat": lat2,
        "to_lng": lon2,
        "polyline_coords": poly,
        "duration": dur_mins + 5,
        "cost": 5000
    }
    
    return [
        {
            "option_name": "Nhanh nhất (Buýt / OSRM)",
            "origin": start_name,
            "destination": end_name,
            "origin_lat": lat1,
            "origin_lng": lon1,
            "dest_lat": lat2,
            "dest_lng": lon2,
            "total_time": dur_mins,
            "total_cost": 7000,
            "transfers": 0,
            "walk_km": 0.3,
            "co2_kg": round(dur_mins * 0.1, 2),
            "steps": [step_bus]
        },
        {
            "option_name": "Rẻ nhất (Buýt kết hợp đi bộ)",
            "origin": start_name,
            "destination": end_name,
            "origin_lat": lat1,
            "origin_lng": lon1,
            "dest_lat": lat2,
            "dest_lng": lon2,
            "total_time": dur_mins + 8,
            "total_cost": 7000,
            "transfers": 0,
            "walk_km": 0.5,
            "co2_kg": round(dur_mins * 0.08, 2),
            "steps": [step_bus]
        },
        {
            "option_name": "Xanh nhất (Xe đạp TNGO)",
            "origin": start_name,
            "destination": end_name,
            "origin_lat": lat1,
            "origin_lng": lon1,
            "dest_lat": lat2,
            "dest_lng": lon2,
            "total_time": dur_mins + 10,
            "total_cost": 5000,
            "transfers": 0,
            "walk_km": 0.2,
            "co2_kg": 0.0,
            "steps": [step_eco]
        }
    ]
