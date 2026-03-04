"""
Vercel Python 서버리스 함수 진입점.

Vercel은 이 파일에서 `app` (ASGI) 변수를 자동으로 감지합니다.
모든 HTTP 요청은 vercel.json 의 rewrites 설정에 따라 여기로 라우팅됩니다.
"""
from src.main import app  # noqa: F401  (Vercel이 `app` 변수를 사용)
