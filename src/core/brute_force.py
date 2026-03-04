import time
from collections import defaultdict

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60  # 15분


class BruteForceProtector:
    def __init__(self) -> None:
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._locked_until: dict[str, float] = {}

    def is_locked(self, key: str) -> tuple[bool, int]:
        """잠김 여부와 남은 초를 반환."""
        locked_until = self._locked_until.get(key, 0.0)
        now = time.time()
        if locked_until > now:
            return True, int(locked_until - now)
        return False, 0

    def record_failure(self, key: str) -> None:
        now = time.time()
        window_start = now - LOCKOUT_SECONDS
        self._attempts[key] = [t for t in self._attempts[key] if t > window_start]
        self._attempts[key].append(now)
        if len(self._attempts[key]) >= MAX_ATTEMPTS:
            self._locked_until[key] = now + LOCKOUT_SECONDS
            self._attempts[key] = []

    def record_success(self, key: str) -> None:
        self._attempts.pop(key, None)
        self._locked_until.pop(key, None)

    def remaining_attempts(self, key: str) -> int:
        return max(0, MAX_ATTEMPTS - len(self._attempts.get(key, [])))


brute_force = BruteForceProtector()
