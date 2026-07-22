import random
from typing import Dict, Any, List

class BikeService:
    def __init__(self):
        # Mock Data cho hệ thống TNGo (Hà Nội & HCM)
        self.stations = [
            {"id": "B01", "name": "Trạm ĐH Quốc Gia HN", "lat": 21.037, "lng": 105.782, "total_docks": 20, "bikes_available": 15},
            {"id": "B02", "name": "Trạm Ga Cát Linh", "lat": 21.0278, "lng": 105.8290, "total_docks": 15, "bikes_available": 2},
            {"id": "B03", "name": "Trạm Hồ Gươm", "lat": 21.0285, "lng": 105.852, "total_docks": 30, "bikes_available": 0}, # Hết xe
            {"id": "B04", "name": "Trạm Bến xe Mỹ Đình", "lat": 21.0289, "lng": 105.7783, "total_docks": 10, "bikes_available": 5},
            {"id": "B05", "name": "Trạm Chợ Bến Thành (HCM)", "lat": 10.7716, "lng": 106.6967, "total_docks": 25, "bikes_available": 20},
            {"id": "B06", "name": "Trạm Phố đi bộ Nguyễn Huệ", "lat": 10.7745, "lng": 106.703, "total_docks": 15, "bikes_available": 10},
        ]
        
        self.pricing = {
            "30_mins": 5000,
            "60_mins": 10000,
            "daily": 50000,
            "monthly": 200000
        }
        
        self.faqs = [
            {"q": "Làm sao để thuê xe?", "a": "Tải ứng dụng TNGo, nạp tiền vào ví, quét mã QR trên xe để mở khóa."},
            {"q": "Tôi có thể trả xe ở trạm khác không?", "a": "Có, bạn có thể thuê xe ở một trạm và trả ở bất kỳ trạm TNGo nào khác còn trống chỗ."},
            {"q": "Khu vực hoạt động của xe đạp là ở đâu?", "a": "Hiện tại xe đạp TNGo hoạt động chủ yếu ở các quận trung tâm Hà Nội (Đống Đa, Ba Đình, Hoàn Kiếm, Tây Hồ) và TP.HCM (Quận 1, 3)."}
        ]

    def _haversine(self, lat1, lon1, lat2, lon2):
        import math
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
            * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def find_nearest_station(self, lat: float, lng: float, need_bike: bool = True) -> Dict[str, Any]:
        """Tìm trạm xe đạp gần nhất. Nếu need_bike = True, bỏ qua các trạm hết xe."""
        nearest = None
        min_dist = float('inf')
        
        for station in self.stations:
            if need_bike and station["bikes_available"] == 0:
                continue
            if not need_bike and (station["total_docks"] - station["bikes_available"] == 0):
                continue
                
            dist = self._haversine(lat, lng, station["lat"], station["lng"])
            if dist < min_dist:
                min_dist = dist
                nearest = station
                
        if not nearest:
            return {"error": "Không tìm thấy trạm xe đạp nào phù hợp gần đây."}
            
        return {
            "station": nearest,
            "distance_km": round(min_dist, 2),
            "walk_time_mins": int(min_dist / 5.0 * 60)
        }

    def get_pricing_info(self) -> str:
        return (
            f"Giá thuê xe đạp công cộng:\n"
            f"- 30 phút: {self.pricing['30_mins']}đ\n"
            f"- 60 phút: {self.pricing['60_mins']}đ\n"
            f"- Vé ngày: {self.pricing['daily']}đ\n"
            f"- Vé tháng: {self.pricing['monthly']}đ"
        )
        
    def get_faqs(self) -> List[Dict[str, str]]:
        return self.faqs

bike_service = BikeService()
