import httpx
from core.enums import OperationMode, NetworkStatus
from config import settings
from logger import get_logger

logger = get_logger(__name__)

# Basic in-memory circuit breaker / health state
_current_network_status = NetworkStatus.ONLINE
_consecutive_failures = 0
MAX_FAILURES = 3

async def check_network_status() -> NetworkStatus:
    """
    Check if we can reach the outside world or APIs.
    Updates the circuit breaker state.
    """
    global _current_network_status, _consecutive_failures
    
    # Check Google DNS as a simple ping, or an actual API
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.head("https://1.1.1.1")
            if resp.status_code == 200:
                _consecutive_failures = 0
                _current_network_status = NetworkStatus.ONLINE
                return _current_network_status
    except Exception as e:
        logger.warning(f"[Network] Ping failed: {e}")
        
    _consecutive_failures += 1
    if _consecutive_failures >= MAX_FAILURES:
        _current_network_status = NetworkStatus.OFFLINE
    else:
        _current_network_status = NetworkStatus.DEGRADED
        
    return _current_network_status

async def select_operation_mode(mode_override: OperationMode = None) -> OperationMode:
    """
    Determine the actual operation mode to use for processing the request.
    If override is provided (e.g. from header or request body), use it.
    Otherwise, determine based on global settings and current network status.
    """
    if mode_override:
        return mode_override
        
    global_mode = settings.operation_mode
    
    if global_mode == OperationMode.OFFLINE:
        return OperationMode.OFFLINE
        
    if global_mode == OperationMode.ONLINE:
        return OperationMode.ONLINE
        
    if global_mode == OperationMode.HYBRID:
        status = await check_network_status()
        if status == NetworkStatus.OFFLINE:
            logger.info("Hybrid mode falling back to OFFLINE due to network status.")
            return OperationMode.OFFLINE
        else:
            return OperationMode.ONLINE

    return OperationMode.ONLINE
