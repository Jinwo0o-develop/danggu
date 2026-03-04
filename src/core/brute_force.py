"""
BruteForceProtector — Upstash Redis 기반 브루트포스 보호.

Redis 미설정 시 인메모리 dict로 폴백한다.
(서버리스 환경에서는 인스턴스 간 공유가 없으므로 데모 목적으로만 사용)
"""
import json
import time

from src.core.redis_client import get_redis

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60  # 15분


class BruteForceProtector:
    def __init__(self) -> None:
        self._r = get_redis()
        self._mem: dict[str, dict] = {}  # Redis 미설정 시 인메모리 폴백

    def _key(self, ip: str) -> str:
        return f"bf:{ip}"

    def _get_info(self, ip: str) -> dict:
        if self._r is not None:
            raw = self._r.get(self._key(ip))
            return json.loads(raw) if raw else {"attempts": [], "locked_until": 0}
        return self._mem.get(ip, {"attempts": [], "locked_until": 0})

    def _set_info(self, ip: str, info: dict) -> None:
        if self._r is not None:
            self._r.set(self._key(ip), json.dumps(info), ex=LOCKOUT_SECONDS)
        else:
            self._mem[ip] = info

    def is_locked(self, key: str) -> tuple[bool, int]:
        """잠김 여부와 남은 초를 반환."""
        info = self._get_info(key)
        locked_until = info.get("locked_until", 0)
        now = time.time()
        if locked_until > now:
            return True, int(locked_until - now)
        return False, 0

    def record_failure(self, key: str) -> None:
        now = time.time()
        info = self._get_info(key)
        window_start = now - LOCKOUT_SECONDS
        info["attempts"] = [t for t in info["attempts"] if t > window_start]
        info["attempts"].append(now)
        if len(info["attempts"]) >= MAX_ATTEMPTS:
            info["locked_until"] = now + LOCKOUT_SECONDS
            info["attempts"] = []
        self._set_info(key, info)

    def record_success(self, key: str) -> None:
        if self._r is not None:
            self._r.delete(self._key(key))
        else:
            self._mem.pop(key, None)

    def remaining_attempts(self, key: str) -> int:
        info = self._get_info(key)
        return max(0, MAX_ATTEMPTS - len(info.get("attempts", [])))


brute_force = BruteForceProtector()
