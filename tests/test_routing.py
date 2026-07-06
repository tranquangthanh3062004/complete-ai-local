import pytest
from services.route_planner import find_route

def test_find_route_success():
    # Test valid route in HCM
    result = find_route("Sân bay Tân Sơn Nhất", "Bến Thành")
    assert "error" not in result
    assert result["origin"] == "Sân bay Tân Sơn Nhất"
    assert result["destination"] == "Bến Thành"
    assert result["total_time"] > 0
    assert result["total_cost"] > 0
    assert len(result["steps"]) > 0

def test_find_route_not_found():
    # Test unknown route
    result = find_route("Địa điểm ảo", "Bến Thành")
    assert "error" in result

def test_find_route_hn():
    # Test valid route in HN
    result = find_route("Cát Linh", "Hà Đông")
    assert "error" not in result
    assert result["origin"] == "Cát Linh"
    assert result["destination"] == "Hà Đông"
    assert result["total_time"] == 25
    assert result["total_cost"] == 15000
