"""
데이터 디렉토리 경로 중앙 관리 모듈.

Vercel 서버리스 환경에서는 /var/task/ (배포 루트)가 읽기 전용이므로,
쓰기 가능한 /tmp/ 를 사용한다.
로컬 개발 환경에서는 프로젝트 루트의 data/ 를 사용한다.

Vercel은 모든 함수 실행 시 자동으로 VERCEL=1 환경변수를 주입한다.
"""
import os
from pathlib import Path

DATA_DIR: Path = Path("/tmp/data") if os.getenv("VERCEL") else Path("data")
