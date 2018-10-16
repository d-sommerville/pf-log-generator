import time
import itertools
import threading


class TimedCache:
    """
    Thread-safe timed cache to store recent transaction counts for mock hosts
    """

    class _CacheEntry:

        def __init__(self, value, ttl):
            self.value = value
            self.expires_at = time.time() + ttl
            self._expired = False

        def is_expired(self):
            return self._expired or self.expires_at < time.time()

    def __init__(self, ttl=30):
        self._entries = []
        self.lock = threading.RLock()
        self.ttl = ttl

    def add(self, value):
        with self.lock:
            self._entries.append(self._CacheEntry(value, self.ttl))

    def entries(self):
        with self.lock:
            self._entries = list(itertools.dropwhile(lambda x: x.is_expired(), self._entries))
            return self._entries
