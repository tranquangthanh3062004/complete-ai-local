import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_chat_direct_online_info():
    response = client.post(
        "/api/chat/direct",
        json={"query": "Tàu điện ngầm Cát Linh Hà Đông giá bao nhiêu?"},
        headers={"X-Network-Mode": "online"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "info"
    assert "reply" in data

def test_chat_direct_offline_route():
    response = client.post(
        "/api/chat/direct",
        json={"query": "Đi từ Bến xe Mỹ Đình đến Hồ Gươm"},
        headers={"X-Network-Mode": "offline"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "route"
    assert "reply" in data
    assert data["mode"] == "offline"
