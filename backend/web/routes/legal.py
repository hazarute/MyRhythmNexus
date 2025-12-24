from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="backend/web/templates")
router = APIRouter(prefix="/legal", tags=["web-legal"])


@router.get("/terms", response_class=HTMLResponse)
async def web_terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})


@router.get("/privacy", response_class=HTMLResponse)
async def web_privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})
