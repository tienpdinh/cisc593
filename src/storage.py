from gevent.lock import RLock
import time
from typing import Any, Dict, Tuple

class CommandError(Exception):
    """Raised when a command cannot be processed."""
    pass

class KeyValueStore:
    """Thread-safe key-value store with memory limits."""
    
    def __init__(self, max_memory_mb: int = 100):
        self._data: Dict[str, Tuple[Any, float]] = {}  # (value, timestamp)
        self._lock = RLock()
        self._max_memory = max_memory_mb * 1024 * 1024

    def get(self, key: str) -> Any:
        with self._lock:
            item = self._data.get(key)
            return item[0] if item else None

    def set(self, key: str, value: Any) -> bool:
        with self._lock:
            self._data[key] = (value, time.time())

            if len(str(value)) > self._max_memory:
                raise CommandError('Value too large')
                
            while self._estimate_memory_usage() > self._max_memory:
                if not self._evict_oldest():
                    raise CommandError('Cannot free enough memory')
                    
            return True

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._data.pop(key, None) is not None

    def flush(self) -> int:
        with self._lock:
            count = len(self._data)
            self._data.clear()
            return count

    def _estimate_memory_usage(self) -> int:
        return sum(len(str(v)) + len(k) for k, (v, _) in self._data.items())

    def _evict_oldest(self) -> bool:
        if not self._data:
            return False
        oldest_key = min(self._data.items(), key=lambda x: x[1][1])[0]
        del self._data[oldest_key]
        return True