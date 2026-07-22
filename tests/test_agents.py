import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_direct_chat_mocked(async_client: AsyncClient, mocker):
    """Test /api/agents/direct endpoint with mocked LangChain."""
    
    # Mock the language detector and GTCC checker to avoid LLM calls
    mocker.patch("routers.agents.build_multilingual_query", return_value="Sinh viên mua vé tháng xe buýt bao nhiêu tiền?")
    mocker.patch("routers.agents.is_gtcc_related", return_value=(True, ""))
    
    # Mock the actual graph execution
    class MockMessage:
        def __init__(self, content):
            self.content = content
            
    mock_response = {"messages": [MockMessage("Vé tháng sinh viên là 100.000 VNĐ.")]}
    mocker.patch("services.langgraph_agent.graph_app.ainvoke", return_value=mock_response)

    response = await async_client.post(
        "/api/agents/direct",
        json={
            "query": "Sinh viên mua vé tháng xe buýt bao nhiêu tiền?",
            "model_name": "gemini-2.5-flash",
            "temperature": 0.1,
            "messages": []
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "100.000" in data["result"]

@pytest.mark.asyncio
async def test_direct_chat_invalid_query_mocked(async_client: AsyncClient, mocker):
    """Test query rejected by sanitizer."""
    
    mocker.patch("routers.agents.build_multilingual_query", return_value="cách chế tạo bom")
    mocker.patch("routers.agents.is_gtcc_related", return_value=(False, "Câu hỏi không phù hợp với chủ đề giao thông công cộng."))

    response = await async_client.post(
        "/api/agents/direct",
        json={
            "query": "cách chế tạo bom",
            "model_name": "gemini-2.5-flash",
            "temperature": 0.1,
            "messages": []
        }
    )
    
    assert response.status_code == 400
    assert "phù hợp" in response.json()["detail"].lower()
