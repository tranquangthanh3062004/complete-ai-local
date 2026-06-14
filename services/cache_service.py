"""
Cache Service v1.0 — In-memory LRU Cache cho GTCC Bot
Thay thế Redis bằng in-memory cache nhẹ, không cần cài thêm dependency.
Tự động expire sau TTL giây.
"""
import time
import hashlib
from collections import OrderedDict
from threading import Lock
from logger import get_logger

logger = get_logger("cache_service")


class TTLCache:
    """Thread-safe LRU cache với tự động expire theo thời gian."""

    def __init__(self, maxsize: int = 256, ttl: int = 3600):
        self._cache: OrderedDict[str, tuple] = OrderedDict()
        self._maxsize = maxsize
        self._ttl = ttl          # seconds
        self._lock = Lock()
        self.hits = 0
        self.misses = 0

    def _make_key(self, text: str) -> str:
        return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()[:16]

    def get(self, key: str) -> str | None:
        hk = self._make_key(key)
        with self._lock:
            if hk not in self._cache:
                self.misses += 1
                return None
            value, ts = self._cache[hk]
            if time.time() - ts > self._ttl:
                del self._cache[hk]
                self.misses += 1
                return None
            # LRU: đưa lên đầu
            self._cache.move_to_end(hk)
            self.hits += 1
            logger.debug(f"[Cache] HIT for key: {hk}")
            return value

    def set(self, key: str, value: str):
        hk = self._make_key(key)
        with self._lock:
            if hk in self._cache:
                self._cache.move_to_end(hk)
            self._cache[hk] = (value, time.time())
            if len(self._cache) > self._maxsize:
                evicted = self._cache.popitem(last=False)
                logger.debug(f"[Cache] Evicted LRU key: {evicted[0]}")

    def clear(self):
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0

    @property
    def stats(self) -> dict:
        total = self.hits + self.misses
        return {
            "size": len(self._cache),
            "maxsize": self._maxsize,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{self.hits / total * 100:.1f}%" if total > 0 else "N/A",
            "ttl_seconds": self._ttl,
        }


# ── Singleton instance dùng chung toàn app ────────────────────────────────────
# TTL 2 giờ, giữ 256 câu trả lời phổ biến nhất
_rag_cache = TTLCache(maxsize=256, ttl=7200)
_agent_cache = TTLCache(maxsize=128, ttl=3600)


def get_rag_cache() -> TTLCache:
    return _rag_cache


def get_agent_cache() -> TTLCache:
    return _agent_cache
