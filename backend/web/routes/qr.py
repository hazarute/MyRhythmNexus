"""
QR Bridge Route
Kullanıcıları QR kod taramasından sonra Chrome tarayıcısına yönlendirmek için kullanılır.
"""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="backend/web/templates")


@router.get("/qr-bridge", response_class=HTMLResponse)
async def qr_bridge(request: Request, target: str | None = Query(None)):
    """
    QR Kod köprü sayfası.
    Kullanıcı QR kodu okuttuğunda (Instagram, iOS Camera vb.) eğer Chrome değilse,
    bu sayfa JS ile intent/scheme kullanarak Chrome'u açmaya zorlar.
    
    Örnek Kullanım:
    https://site.com/web/qr-bridge?target=/web/subscription/123
    """
    
    # Hedef URL belirlenir, yoksa dashboard'a atılır
    target_url = target if target else "/web/dashboard"
    
    # Absolute URL oluşturma (JS tarafında da kontrol var ama burada da yapalım)
    if not target_url.startswith("http"):
        # request.base_url genelde protocol+host+port döner (örn: http://localhost:8000/)
        base_url = str(request.base_url).rstrip("/")
        if not target_url.startswith("/"):
            target_url = "/" + target_url
        target_url = f"{base_url}{target_url}"

    return templates.TemplateResponse(
        "qr_bridge.html",
        {
            "request": request,
            "target_url": target_url
        }
    )
