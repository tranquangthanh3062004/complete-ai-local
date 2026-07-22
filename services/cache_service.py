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

class SemanticCache:
    """Cache dựa trên ý nghĩa (Vector Similarity)."""
    
    def __init__(self, threshold=0.92, maxsize=256):
        self._entries = []
        self._maxsize = maxsize
        self._threshold = threshold
        self._lock = Lock()
        self.hits = 0
        self.misses = 0
        
    def _cosine_similarity(self, v1, v2):
        import math
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_v1 = math.sqrt(sum(a * a for a in v1))
        norm_v2 = math.sqrt(sum(b * b for b in v2))
        if norm_v1 == 0 or norm_v2 == 0: return 0.0
        return dot_product / (norm_v1 * norm_v2)

    def get(self, query: str) -> str | None:
        try:
            from services.ai_rag import get_embeddings
            embedder = get_embeddings()
            if not embedder: return None
            
            query_emb = embedder.embed_query(query)
            
            best_score = -1.0
            best_ans = None
            
            with self._lock:
                for emb, ans in self._entries:
                    score = self._cosine_similarity(query_emb, emb)
                    if score > best_score:
                        best_score = score
                        best_ans = ans
                        
                if best_score >= self._threshold:
                    self.hits += 1
                    logger.debug(f"[SemanticCache] HIT score {best_score:.3f} for '{query[:40]}'")
                    return best_ans
                    
                self.misses += 1
                return None
        except Exception as e:
            logger.warning(f"Semantic Cache Get Error: {e}")
            return None

    def set(self, query: str, value: str):
        try:
            from services.ai_rag import get_embeddings
            embedder = get_embeddings()
            if not embedder: return
            
            query_emb = embedder.embed_query(query)
            
            with self._lock:
                if len(self._entries) >= self._maxsize:
                    self._entries.pop(0) # FIFO eviction
                self._entries.append((query_emb, value))
        except Exception as e:
            logger.warning(f"Semantic Cache Set Error: {e}")


# ── Singleton instance dùng chung toàn app ────────────────────────────────────
# TTL 2 giờ, giữ 256 câu trả lời phổ biến nhất
_rag_cache = TTLCache(maxsize=256, ttl=7200)
_agent_cache = TTLCache(maxsize=128, ttl=3600)
_semantic_cache = SemanticCache(threshold=0.92, maxsize=256)

def get_rag_cache() -> TTLCache:
    return _rag_cache

def get_agent_cache() -> TTLCache:
    return _agent_cache

def get_semantic_cache() -> SemanticCache:
    return _semantic_cache
