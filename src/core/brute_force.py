"""
BruteForceProtector — Upstash Redis 기반 브루트포스 보호.

서버리스 환경에서도 인스턴스 간 상태를 공유하기 위해
인메모리 dict 대신 Upstash Redis(HTTP REST)를 사용한다.
"""
import json
import time

from src.core.redis_client import get_redis

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60  # 15분


class BruteForceProtector:
    def __init__(self) -> None:
        self._r = get_redis()

    def _key(self, ip: str) -> str:
        return f"bf:{ip}"

    def is_locked(self, key: str) -> tuple[bool, int]:
        """잠김 여부와 남은 초를 반환."""
        raw = self._r.get(self._key(key))
        if not raw:
            return False, 0
        info = json.loads(raw)
        locked_until = info.get("locked_until", 0)
        now = time.time()
        if locked_until > now:
            return True, int(locked_until - now)
        return False, 0

    def record_failure(self, key: str) -> None:
        now = time.time()
        raw = self._r.get(self._key(key))
        info = json.loads(raw) if raw else {"attempts": [], "locked_until": 0}

        # 윈도우 밖 시도 제거
        window_start = now - LOCKOUT_SECONDS
        info["attempts"] = [t for t in info["attempts"] if t > window_start]
        info["attempts"].append(now)

        if len(info["attempts"]) >= MAX_ATTEMPTS:
            info["locked_until"] = now + LOCKOUT_SECONDS
            info["attempts"] = []

        self._r.set(self._key(key), json.dumps(info), ex=LOCKOUT_SECONDS)

    def record_success(self, key: str) -> None:
        self._r.delete(self._key(key))

    def remaining_attempts(self, key: str) -> int:
        raw = self._r.get(self._key(key))
        if not raw:
            return MAX_ATTEMPTS
        info = json.loads(raw)
        return max(0, MAX_ATTEMPTS - len(info.get("attempts", [])))


brute_force = BruteForceProtector()
