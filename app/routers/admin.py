"""
Admin routes - serves admin dashboard and application management pages.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.data.demo_data import APPLICATIONS

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")
settings = get_settings()


def _get_stats() -> dict:
    """Calculate application counts by status."""
    pending = sum(1 for app in APPLICATIONS if app['status'] == 'Pending')
    in_progress = sum(1 for app in APPLICATIONS if app['status'] == 'In Progress')
    completed = sum(1 for app in APPLICATIONS if app['status'] == 'Completed')
    return {
        'pending': pending,
        'in_progress': in_progress,
        'completed': completed,
        'total': len(APPLICATIONS)
    }


@router.get("", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    """Serve the admin dashboard page."""
    stats = _get_stats()
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "app_name": settings.APP_NAME,
            "theme_css": f"css/style_{settings.APP_THEME}.css",
            "stats": stats,
            "applications": APPLICATIONS
        }
    )


@router.get("/api/stats")
def get_stats():
    """Return dashboard statistics as JSON."""
    return _get_stats()


@router.get("/api/applications")
def get_applications():
    """Return all applications as JSON."""
    return {"applications": APPLICATIONS}
