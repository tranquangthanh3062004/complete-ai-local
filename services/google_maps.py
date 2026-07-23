import os
import googlemaps
from datetime import datetime
from config import settings
from logger import get_logger
logger = get_logger(__name__)

class GoogleMapsService:
    def __init__(self):
        self.api_key = getattr(settings, 'google_maps_api_key', os.getenv('GOOGLE_MAPS_API_KEY'))
        self.client = None
        if self.api_key:
            try:
                import googlemaps
                self.client = googlemaps.Client(key=self.api_key)
            except Exception as e:
                logger.warning(f"[Google Maps] Could not initialize googlemaps client: {e}")
        
    def get_directions(self, origin: str, destination: str, mode: str = "transit") -> str:
        """
        Get directions between two points using Google Maps API.
        Supported modes: driving, walking, bicycling, transit
        """
        if not self.client:
            logger.warning("[Google Maps] API Key not found, using fallback logic.")
            return self._fallback_directions(origin, destination, mode)
            
        try:
            now = datetime.now()
            directions_result = self.client.directions(
                origin,
                destination,
                mode=mode,
                departure_time=now,
                language="vi"
            )
            
            if not directions_result:
                return "Không tìm thấy lộ trình phù hợp."
                
            route = directions_result[0]['legs'][0]
            distance = route['distance']['text']
            duration = route['duration']['text']
            steps = []
            
            for step in route['steps']:
                instructions = step['html_instructions'].replace("<b>", "**").replace("</b>", "**").replace("<div style=\"font-size:0.9em\">", " (").replace("</div>", ")")
                # Remove any leftover HTML tags and decode HTML entities
                import re, html
                instructions = re.sub('<[^<]+?>', '', instructions)
                instructions = html.unescape(instructions)
                steps.append(f"- {instructions} ({step['distance']['text']})")
                
            steps_str = "\n".join(steps)
            
            # Calculate estimated Carbon Emission
            carbon_str = self._calculate_carbon(distance, mode)
            
            return f"**Lộ trình từ {origin} đến {destination} (bằng {mode}):**\n- Quãng đường: {distance}\n- Thời gian: {duration}\n- Phát thải Carbon ước tính: {carbon_str}\n\n**Chi tiết:**\n{steps_str}"
            
        except Exception as e:
            logger.error(f"[Google Maps] Error fetching directions: {e}")
            return self._fallback_directions(origin, destination, mode)
            
    def get_distance_matrix(self, origins: list, destinations: list, mode: str = "transit") -> dict:
        """Get distance matrix for multiple origins and destinations."""
        if not self.client:
            return {"error": "API Key not configured."}
        try:
            return self.client.distance_matrix(origins, destinations, mode=mode, language="vi")
        except Exception as e:
            logger.error(f"[Google Maps] Distance Matrix Error: {e}")
            return {"error": str(e)}

    def _calculate_carbon(self, distance_text: str, mode: str) -> str:
        try:
            # Parse distance e.g. "5.2 km" -> 5.2
            km = float(distance_text.lower().replace("km", "").replace(",", ".").strip())
            # Average CO2 emissions per passenger-km (g CO2)
            rates = {
                "transit": 68,
                "driving": 192,
                "bicycling": 0,
                "walking": 0
            }
            rate = rates.get(mode, 100)
            carbon_g = km * rate
            if carbon_g == 0:
                return "0g CO2 🍃 (Thân thiện với môi trường)"
            if carbon_g < 1000:
                return f"{carbon_g:.0f}g CO2"
            return f"{(carbon_g/1000):.1f}kg CO2"
        except:
            return "Không xác định"
            
    def _fallback_directions(self, origin: str, destination: str, mode: str = "transit") -> str:
        """
        Fallback using OpenStreetMap (Nominatim + OSRM) when Google Maps API Key is missing.
        Completely free, accurate road network routing.
        """
        import httpx
        import re

        def _geocode_or_coords(client, text: str):
            text = text.strip()
            text_lower = text.lower()

            # Vị trí tương đối mặc định về trung tâm Giao thông (Ga Hà Nội)
            relative_locations = ["vị trí hiện tại", "ở đây", "tại đây", "hiện tại", "điểm đi", "my location"]
            if any(rel == text_lower or rel in text_lower for rel in relative_locations):
                return 21.0253, 105.8415  # Tọa độ Ga Hà Nội (Trung tâm GTCC)

            match = re.match(r"^\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*$", text)
            if match:
                return float(match.group(1)), float(match.group(2))
                
            headers = {"User-Agent": "COMPLETE-AI-Transit/5.1"}
            search_q = text if "hà nội" in text_lower or "hanoi" in text_lower else f"{text}, Hà Nội, Việt Nam"
            try:
                res = client.get("https://nominatim.openstreetmap.org/search", params={"q": search_q, "format": "json", "limit": 1}, headers=headers)
                if res.status_code == 200 and res.json():
                    return float(res.json()[0]["lat"]), float(res.json()[0]["lon"])
            except Exception:
                pass
                
            if search_q != text:
                try:
                    res = client.get("https://nominatim.openstreetmap.org/search", params={"q": text, "format": "json", "limit": 1}, headers=headers)
                    if res.status_code == 200 and res.json():
                        return float(res.json()[0]["lat"]), float(res.json()[0]["lon"])
                except Exception:
                    pass
                    
            return None, None

        try:
            with httpx.Client(timeout=5.0) as client:
                lat1, lon1 = _geocode_or_coords(client, origin)
                lat2, lon2 = _geocode_or_coords(client, destination)
                
                if lat1 is not None and lat2 is not None:
                    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false&steps=true"
                    osrm_res = client.get(osrm_url)
                    if osrm_res.status_code == 200:
                        route_data = osrm_res.json()
                        if route_data.get("routes"):
                            route = route_data["routes"][0]
                            dist_km = round(route["distance"] / 1000, 1)
                            dur_mins = round(route["duration"] / 60)
                            
                            carbon = self._calculate_carbon(f"{dist_km} km", mode)
                            
                            steps = []
                            for s in route.get("legs", [{}])[0].get("steps", [])[:5]:
                                name = s.get("name") or "Đoạn đường tiếp theo"
                                s_dist = round(s.get("distance", 0))
                                if s_dist > 50:
                                    steps.append(f"- Đi theo {name} ({s_dist}m)")
                            
                            steps_str = "\n".join(steps) if steps else "- Di chuyển dọc theo tuyến đường chính"
                            
                            return (
                                f"🗺️ **Lộ trình thực tế (OpenStreetMap / OSRM):**\n"
                                f"📍 **Điểm đi:** {origin.title()}\n"
                                f"🏁 **Điểm đến:** {destination.title()}\n"
                                f"📏 **Quãng đường:** {dist_km} km\n"
                                f"⏱️ **Thời gian ước tính:** ~{dur_mins} phút\n"
                                f"🌱 **Phát thải CO2:** {carbon}\n\n"
                                f"**Chi tiết di chuyển:**\n{steps_str}\n\n"
                                f"💡 *Gợi ý:* Bạn có thể đón xe buýt kết hợp đi bộ 5-10 phút để tối ưu chi phí."
                            )
        except Exception as e:
            logger.error(f"[OSM Fallback Error]: {e}")

        return (
            f"🗺️ **Thông tin hành trình từ {origin.title()} đến {destination.title()}:**\n"
            f"📍 **Điểm đi:** {origin.title()}\n"
            f"🏁 **Điểm đến:** {destination.title()}\n"
            f"🚌 **Gợi ý phương tiện:** Xe buýt 01, 02, 08A, 26, 31 kết hợp Metro 2A & Xe đạp công cộng TNGO."
        )

gmaps_service = GoogleMapsService()
