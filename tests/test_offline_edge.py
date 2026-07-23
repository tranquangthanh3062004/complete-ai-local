import pytest
from offline_edge.edge_rag import search_offline_knowledge

def test_offline_knowledge_search():
    res = search_offline_knowledge("Giá vé xe buýt sinh viên")
    assert "100.000" in res or "vé" in res.lower() or "sinh viên" in res.lower()

def test_offline_metro_search():
    res = search_offline_knowledge("Metro Cát Linh Hà Đông")
    assert "Cát Linh" in res or "2A" in res or "12 ga" in res

def test_offline_airport_search():
    res = search_offline_knowledge("Xe buýt đi Sân bay Nội Bài 86")
    assert "86" in res or "Nội Bài" in res or "45.000" in res

@pytest.mark.asyncio
async def test_edge_gateway_chat_endpoint():
    from offline_edge.edge_gateway import app
    from httpx import AsyncClient, ASGITransport
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testedge") as client:
        res = await client.post("/api/chat", json={"query": "Giá vé xe buýt Hà Nội"})
        assert res.status_code == 200
        data = res.json()
        assert "reply" in data or "result" in data
