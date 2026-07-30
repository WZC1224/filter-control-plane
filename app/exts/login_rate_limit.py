"""登录滑动窗口限流（进程内；多 worker 各算各的）。"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def allow(self, key: str, *, max_hits: int, window_seconds: float) -> bool:
        """记录一次尝试；超限返回 False（本次不计入）。max_hits<=0 表示关闭。"""
        if max_hits <= 0:
            return True
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            q = self._hits[key]
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= max_hits:
                return False
            q.append(now)
            return True


login_limiter = SlidingWindowLimiter()
