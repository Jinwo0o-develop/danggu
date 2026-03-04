"""
미디어 파일 업로드 처리 모듈.

Factory Method 패턴 적용:
  save_uploads()가 각 파일에 대해 UUID 파일명을 생성(Factory)하여
  일관된 저장 경로를 반환한다.
"""
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

MEDIA_DIR = Path("data/media")
ALLOWED_MIME_PREFIXES = ("image/", "video/")


def save_uploads(files: list[UploadFile]) -> list[str]:
    """허용된 MIME 타입의 파일을 저장하고 상대 경로 목록을 반환."""
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for upload in files:
        if not upload.filename:
            continue
        mime = upload.content_type or ""
        if not any(mime.startswith(p) for p in ALLOWED_MIME_PREFIXES):
            continue
        suffix = Path(upload.filename).suffix
        unique_name = f"{uuid.uuid4().hex}{suffix}"
        dest = MEDIA_DIR / unique_name
        with dest.open("wb") as f:
            shutil.copyfileobj(upload.file, f)
        paths.append(f"data/media/{unique_name}")
    return paths
