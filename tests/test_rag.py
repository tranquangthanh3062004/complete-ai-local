import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_search_knowledge_base_mocked(async_client: AsyncClient, mocker):
    """Test the RAG chat endpoint with a mocked retriever."""
    
    mock_docs = [
        type("MockDoc", (object,), {"page_content": "Tuyến xe buýt 01 đi qua bến xe Gia Lâm.", "metadata": {"source": "hanoi_bus_routes.txt"}})()
    ]
    
    # Mock retriever
    mock_retriever = mocker.MagicMock()
    mock_retriever.invoke.return_value = mock_docs
    
    # Mock vector store
    mock_vs = mocker.MagicMock()
    mock_vs.similarity_search.return_value = mock_docs
    mock_vs.as_retriever.return_value = mock_retriever
    
    mocker.patch("routers.rag.get_vector_store", return_value=mock_vs)
    
    # Mock sanitizer and LLM
    mocker.patch("services.sanitizer.sanitize_query", return_value=("Tuyến xe buýt 01 đi qua đâu?", True, ""))
    
    # We should mock the LLM chain or cache to avoid calling LLM
    mock_cache = mocker.MagicMock()
    mock_cache.get.return_value = "Tuyến xe buýt 01 đi qua bến xe Gia Lâm."
    mocker.patch("services.cache_service.get_rag_cache", return_value=mock_cache)
    
    response = await async_client.post(
        "/api/documents/chat/",
        json={
            "query": "Tuyến xe buýt 01 đi qua đâu?"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "Gia Lâm" in data["response"]
