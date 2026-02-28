import time
import logging
from collections import OrderedDict
from typing import Optional

from config import CACHE_MAX_SIZE, CACHE_TTL_HOURS

logger = logging.getLogger(__name__)

class TranscriptCache:
    def __init__(self, max_size: int = CACHE_MAX_SIZE, ttl_hours: int = CACHE_TTL_HOURS):
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: dict[str, float] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_hours * 3600
        self.hits = 0
        self.misses = 0

    def get(self, video_id: str):
        if video_id not in self._cache:
            self.misses += 1
            return None

        if time.time() - self._timestamps[video_id] > self.ttl_seconds:
            self._evict(video_id)
            self.misses += 1
            logger.debug(f"Cache TTL expired for {video_id}")
            return None

        self._cache.move_to_end(video_id)
        self.hits += 1
        logger.debug(f"Cache HIT for {video_id}")
        return self._cache[video_id]

    def set(self, video_id: str, transcript_result) -> None:
        if video_id in self._cache:
            self._cache.move_to_end(video_id)
        else:
            if len(self._cache) >= self.max_size:
                oldest = next(iter(self._cache))
                self._evict(oldest)
                logger.debug(f"Cache LRU eviction: {oldest}")
            self._cache[video_id] = transcript_result

        self._timestamps[video_id] = time.time()
        logger.debug(f"Cache SET for {video_id}")

    def _evict(self, video_id: str) -> None:
        self._cache.pop(video_id, None)
        self._timestamps.pop(video_id, None)

    def clear(self) -> None:
        self._cache.clear()
        self._timestamps.clear()

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def stats(self) -> dict:
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "size": self.size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
        }

transcript_cache = TranscriptCache()
