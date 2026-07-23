import pytest
import httpx
import json
import asyncio
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_sanitize_query():
    from services.sanitizer import sanitize_query
    
    q, safe, reason = sanitize_query("DROP TABLE users;")
    assert not safe, "Phải phát hiện injection"
    
    q, safe, reason = sanitize_query("Giá vé xe buýt?")
    assert safe, "Câu hỏi bình thường phải pass"

def test_detect_topic():
    from services.ai_topic import detect_topic
    assert detect_topic("giá vé và vé tháng liên tuyến") == "ve_gia_cuoc"
    assert detect_topic("luật nồng độ cồn") == "luat_quy_dinh"

def test_extract_intent_regex():
    from services.langgraph_agent import extract_locations_and_intent_regex
    req_map, req_bike, orig, dest, query = extract_locations_and_intent_regex("Chỉ đường từ ngã tư sở đến hồ gươm")
    assert req_map == True
    assert orig.lower() == "ngã tư sở"
    assert dest.lower() == "hồ gươm"
