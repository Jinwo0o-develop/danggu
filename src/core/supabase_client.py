"""Supabase 클라이언트 싱글톤."""
import logging

from supabase import Client, create_client

from src.config import settings

logger = logging.getLogger(__name__)

_client: Client | None = None
_initialized = False


def get_supabase() -> Client | None:
    """Supabase Client 반환. 자격증명 미설정 시 None (데모 모드)."""
    global _client, _initialized
    if not _initialized:
        _initialized = True
        url = settings.supabase_url
        key = settings.supabase_key
        if url and key:
            _client = create_client(url, key)
        else:
            logger.warning(
                "SUPABASE_URL / SUPABASE_KEY 미설정 — 데모 모드로 실행 중. "
                "데이터는 저장되지 않습니다."
            )
    return _client
