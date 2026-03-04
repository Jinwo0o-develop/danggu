import json
from pathlib import Path

DATA_FILE = Path("data/menus.json")


class MenuRepository:
    def __init__(self) -> None:
        DATA_FILE.parent.mkdir(exist_ok=True)
        if not DATA_FILE.exists():
            DATA_FILE.write_text("[]", encoding="utf-8")

    def _load(self) -> list[dict]:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))

    def _save(self, data: list[dict]) -> None:
        DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_all(self) -> list[dict]:
        return self._load()

    def add(self, emoji: str, name: str, desc: str) -> dict:
        menus = self._load()
        new_menu = {"emoji": emoji, "name": name, "desc": desc}
        menus.append(new_menu)
        self._save(menus)
        return new_menu

    def delete(self, name: str) -> bool:
        menus = self._load()
        filtered = [m for m in menus if m["name"] != name]
        if len(filtered) == len(menus):
            return False
        self._save(filtered)
        return True
