from pathlib import Path

from fastapi.templating import Jinja2Templates

from src.core.csrf import csrf_input

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.globals["csrf_input"] = csrf_input


def _mask_phone(phone: str | None) -> str:
    """010-1234-5678  →  010-****-5678 (중간 4자리 마스킹)."""
    if not phone:
        return "—"
    parts = phone.split("-")
    if len(parts) == 3:
        return f"{parts[0]}-****-{parts[2]}"
    # 하이픈 없는 포맷 (01012345678)
    if len(phone) >= 8:
        return phone[:3] + "-****-" + phone[-4:]
    return "****"


templates.env.filters["mask_phone"] = _mask_phone
