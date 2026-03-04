"""
BaseJsonRepository — Template Method 패턴 기반 JSON 파일 저장소 추상 클래스.

모든 리스트 기반 도메인 Repository는 이 클래스를 상속하여
Singleton 보장, _load(), _save(), _next_id() 를 자동으로 얻는다.

사용 예:
    class MyRepo(BaseJsonRepository):
        @property
        def file_path(self) -> Path:
            return Path("data/my_data.json")
"""
import json
from abc import ABC, abstractmethod
from pathlib import Path


class BaseJsonRepository(ABC):
    """
    Template Method Pattern:
      - Singleton 보장 (__new__ + _initialized 플래그)
      - _load() / _save() 공통 구현 (리스트 기반 JSON)
      - file_path 추상 프로퍼티로 파일 위치를 하위 클래스가 지정
      - _write_default()를 오버라이드하면 초기 데이터 커스터마이징 가능
    """

    _instances: dict = {}

    def __new__(cls) -> "BaseJsonRepository":
        if cls not in cls._instances:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[cls] = instance
        return cls._instances[cls]

    def __init__(self) -> None:
        if self._initialized:
            return
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._write_default()
        self._initialized = True

    @property
    @abstractmethod
    def file_path(self) -> Path:
        """JSON 파일 경로 (하위 클래스에서 반드시 지정)."""
        ...

    def _write_default(self) -> None:
        """초기 데이터 파일 생성. 빈 배열이 기본값."""
        self.file_path.write_text("[]", encoding="utf-8")

    def _load(self) -> list[dict]:
        return json.loads(self.file_path.read_text(encoding="utf-8"))

    def _save(self, data: list[dict]) -> None:
        self.file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _next_id(self, items: list[dict]) -> int:
        """items 리스트에서 다음 자동증가 ID를 반환."""
        return max((item.get("id", 0) for item in items), default=0) + 1
