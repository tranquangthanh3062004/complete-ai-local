import pytest
from fastapi.testclient import TestClient
from main import app
from database import async_engine
from models import Base

@pytest.fixture(scope="session")
async def client():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield TestClient(app)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

# More tests: auth, rag, etc.

