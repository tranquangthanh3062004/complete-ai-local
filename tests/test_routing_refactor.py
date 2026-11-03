import pytest
from core.routing.intent import analyze_intent
from core.routing.mode import check_network_status, select_operation_mode
from core.enums import IntentType, OperationMode, NetworkStatus

@pytest.mark.asyncio
async def test_intent_analyzer():
    # 1. Greeting
    intent = await analyze_intent("xin chào")
    assert intent.type == IntentType.GREETING

    # 2. Route
    intent = await analyze_intent("chỉ đường từ Bến xe Mỹ Đình đến Hồ Gươm")
    assert intent.type == IntentType.ROUTE
    assert intent.origin.lower() == "bến xe mỹ đình"
    assert intent.destination.lower() == "hồ gươm"

    # 3. Info
    intent = await analyze_intent("giá vé xe buýt là bao nhiêu?")
    assert intent.type == IntentType.INFO

@pytest.mark.asyncio
async def test_mode_selector():
    # Forced mode override
    mode = await select_operation_mode(OperationMode.OFFLINE)
    assert mode == OperationMode.OFFLINE
