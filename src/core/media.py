"""
미디어 파일 업로드 처리 모듈 — Supabase Storage 기반.

Supabase Storage의 'uploads' 버킷에 파일을 저장하고
공개 URL 목록을 반환한다.
버킷은 Supabase 대시보드에서 Public 버킷으로 미리 생성해야 한다.
"""
import uuid
from pathlib import Path

from fastapi import UploadFile

from src.core.supabase_client import get_supabase

ALLOWED_MIME_PREFIXES = ("image/", "video/")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mov"}
BUCKET = "uploads"


def save_uploads(files: list[UploadFile]) -> list[str]:
    """허용된 MIME 타입 및 확장자의 파일을 Supabase Storage에 저장하고 공개 URL 목록을 반환."""
    client = get_supabase()
    urls: list[str] = []
    for upload in files:
        if not upload.filename:
            continue
        mime = upload.content_type or ""
        if not any(mime.startswith(p) for p in ALLOWED_MIME_PREFIXES):
            continue
        suffix = Path(upload.filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            continue
        file_bytes = upload.file.read()
        dest = f"media/{uuid.uuid4().hex}{suffix}"
        client.storage.from_(BUCKET).upload(dest, file_bytes, {"content-type": mime})
        public_url = client.storage.from_(BUCKET).get_public_url(dest)
        urls.append(public_url)
    return urls
