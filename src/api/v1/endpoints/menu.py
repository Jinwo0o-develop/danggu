import random
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from src.domain.menu.repository import MenuRepository
from src.templates_setup import templates

router = APIRouter()


def get_menu_repository() -> MenuRepository:
    return MenuRepository()


MenuRepo = Annotated[MenuRepository, Depends(get_menu_repository)]


@router.get("/api/random-menu", response_class=HTMLResponse)
async def random_menu(request: Request, repo: MenuRepo) -> HTMLResponse:
    menus = repo.get_all()
    if not menus:
        return HTMLResponse("<p style='color:#f5e6e6'>메뉴가 없습니다. 추가해주세요!</p>")
    menu = random.choice(menus)
    return templates.TemplateResponse(
        "menu_result.html", {"request": request, "menu": menu}
    )


@router.get("/api/menus/add-form", response_class=HTMLResponse)
async def add_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("menu_add_form.html", {"request": request})


@router.post("/api/menus", response_class=HTMLResponse)
async def add_menu(
    request: Request,
    repo: MenuRepo,
    emoji: str = Form(...),
    name: str = Form(...),
    desc: str = Form(...),
) -> HTMLResponse:
    repo.add(emoji=emoji.strip(), name=name.strip(), desc=desc.strip())
    return templates.TemplateResponse(
        "menu_toast.html",
        {"request": request, "message": f"'{name}' 메뉴가 추가됐습니다!"},
    )


@router.get("/api/menus/delete-list", response_class=HTMLResponse)
async def delete_list(request: Request, repo: MenuRepo) -> HTMLResponse:
    menus = repo.get_all()
    return templates.TemplateResponse(
        "menu_delete_list.html", {"request": request, "menus": menus}
    )


@router.delete("/api/menus/{name}", response_class=HTMLResponse)
async def delete_menu(request: Request, name: str, repo: MenuRepo) -> HTMLResponse:
    repo.delete(name)
    menus = repo.get_all()
    return templates.TemplateResponse(
        "menu_delete_list.html", {"request": request, "menus": menus}
    )
