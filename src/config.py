import logging

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_INSECURE_DEFAULT = "dev-secret-key-change-me"


class Settings(BaseSettings):
    app_env: str = "development"  # "production"으로 설정 시 HTTPS 강제
    secret_key: str = _INSECURE_DEFAULT  # .env.local 의 SECRET_KEY 로 반드시 교체
    admin_register_key: str = ""  # 비어 있으면 회원가입 비활성화

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""  # service_role key 권장

    # Upstash Redis
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        if self.secret_key == _INSECURE_DEFAULT:
            if self.is_production:
                raise ValueError(
                    "SECRET_KEY must be set via environment variable in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
            logger.warning(
                "⚠️  SECRET_KEY is using the insecure default. "
                "Set SECRET_KEY in .env.local for persistent sessions."
            )
        return self

    model_config = SettingsConfigDict(env_file=".env.local", env_file_encoding="utf-8")


settings = Settings()
