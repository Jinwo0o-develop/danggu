"""Upstash Redis 클라이언트 싱글톤."""
import logging

from upstash_redis import Redis

from src.config import settings

logger = logging.getLogger(__name__)

_client: Redis | None = None
_initialized = False


def get_redis() -> Redis | None:
    """Redis Client 반환. 자격증명 미설정 시 None (인메모리 폴백)."""
    global _client, _initialized
    if not _initialized:
        _initialized = True
        url = settings.upstash_redis_rest_url
        token = settings.upstash_redis_rest_token
        if url and token:
            _client = Redis(url=url, token=token)
        else:
            logger.warning(
                "UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN 미설정 "
                "— 인메모리 브루트포스 보호 사용 (서버리스 환경에서는 인스턴스 간 공유 없음)"
            )
    return _client
