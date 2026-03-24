"""
Admin routes — separate login session from regular users.
Fetches live transaction data from the IntellectSee platform API.

- GET  /admin/login  → serve admin login page
- POST /admin/login  → validate admin credentials, set admin_logged_in
- POST /admin/logout → clear admin session, redirect to /admin/login
- GET  /admin        → dashboard (requires admin_logged_in)
- GET  /admin/api/*  → JSON endpoints (requires admin_logged_in)
"""

import requests

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.core.dependencies import get_session_manager, get_agent_client
from app.core.logger import get_logger
from app.services.category_service import get_all_categories, get_category_by_slug
from app.services.admin_service import fetch_applications_for_asset, compute_stats
from app.services.rest_client import RestClient

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")
settings = get_settings()
logger = get_logger()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_admin(request: Request):
    """
    Check for an active admin session (admin_logged_in flag).
    Returns (session, session_id, sm, None) if authenticated,
    or (None, None, None, redirect) if not.
    """
    sm = get_session_manager()
    session_id, session = sm.get_session(request)
    if not session.get('admin_logged_in'):
        return None, None, None, RedirectResponse(url="/admin/login", status_code=302)
    return session, session_id, sm, None


def _fetch_live_data_for_category(category: dict):
    """
    Fetch and merge applications for all subcategories of a category.
    Each application is annotated with subcategory_name.
    """
    agent_client = get_agent_client()
    all_applications = []
    for sub in category.get("subcategories", []):
        asset_id = sub.get("asset_id") or ""
        if not asset_id.strip():
            continue
        apps = fetch_applications_for_asset(agent_client, settings, asset_id)
        for app in apps:
            app["subcategory_name"] = sub["name"]
        all_applications.extend(apps)

    all_applications.sort(key=lambda x: x.get("submission_date", ""), reverse=True)
    stats = compute_stats(all_applications)
    return all_applications, stats


# ---------------------------------------------------------------------------
# Admin Login / Logout
# ---------------------------------------------------------------------------

@router.get("/login", response_class=HTMLResponse)
def admin_login_page(request: Request, response: Response):
    """Serve the admin login page. Redirects to dashboard if already logged in."""
    sm = get_session_manager()
    _, session = sm.get_session(request)
    if session.get('admin_logged_in'):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse(
        "admin_login.html",
        {
            "request": request,
            "app_name": settings.APP_NAME,
            "theme_css": f"css/style_{settings.APP_THEME}.css",
            "error": None
        }
    )


@router.post("/login")
async def admin_login_submit(request: Request, response: Response):
    """
    Handle admin login form submission (application/x-www-form-urlencoded).
    Sets admin_logged_in in session and redirects to /admin.
    """
    try:
        form = await request.form()
        username = (form.get('username') or '').strip()
        password = (form.get('password') or '').strip()

        sm = get_session_manager()
        session_id, session = sm.get_session(request)

        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = settings.ADMIN_DISPLAY_NAME
            redirect = RedirectResponse(url="/admin", status_code=303)
            sm.save_session(redirect, session_id)
            logger.info(f"Admin logged in: {username}")
            return redirect

        logger.warning(f"Failed admin login attempt for: {username}")
        resp = templates.TemplateResponse(
            "admin_login.html",
            {
                "request": request,
                "app_name": settings.APP_NAME,
                "theme_css": f"css/style_{settings.APP_THEME}.css",
                "error": "Invalid username or password"
            },
            status_code=401
        )
        return resp

    except Exception as e:
        logger.error(f"Admin login error: {e}")
        return RedirectResponse(url="/admin/login", status_code=302)


@router.post("/logout")
async def admin_logout(request: Request, response: Response):
    """Clear admin session and redirect to admin login page."""
    sm = get_session_manager()
    session_id, session = sm.get_session(request)

    admin_username = session.pop('admin_username', 'Unknown')
    session.pop('admin_logged_in', None)

    redirect = RedirectResponse(url="/admin/login", status_code=303)
    sm.save_session(redirect, session_id)
    logger.info(f"Admin logged out: {admin_username}")
    return redirect


# ---------------------------------------------------------------------------
# Admin Dashboard & API
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Admin Dashboard & API
# ---------------------------------------------------------------------------

@router.get("", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    """Serve the admin dashboard with category cards. Requires admin session."""
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return redirect

    tmpl = templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "app_name": settings.APP_NAME,
            "theme_css": f"css/style_{settings.APP_THEME}.css",
            "username": session.get('admin_username', 'Admin'),
            "view_mode": "dashboard",
            "categories": get_all_categories()
        }
    )
    sm.save_session(tmpl, session_id)
    return tmpl


@router.get("/category/{slug}", response_class=HTMLResponse)
def admin_category_detail(request: Request, slug: str):
    """Serve the admin dashboard category detail view. Requires admin session."""
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return redirect

    category = get_category_by_slug(slug)
    if not category:
        return RedirectResponse(url="/admin", status_code=302)

    tmpl = templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "app_name": settings.APP_NAME,
            "theme_css": f"css/style_{settings.APP_THEME}.css",
            "username": session.get('admin_username', 'Admin'),
            "view_mode": "category",
            "category": category,
        }
    )
    sm.save_session(tmpl, session_id)
    return tmpl


@router.get("/api/categories")
def get_categories(request: Request):
    """Return list of categories. Requires admin session."""
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return JSONResponse(status_code=401, content={"error": "Admin authentication required"})

    resp = JSONResponse({"categories": get_all_categories()})
    sm.save_session(resp, session_id)
    return resp


@router.get("/api/categories/{slug}")
def get_category_data(request: Request, slug: str):
    """Return applications and stats for a specific category. Requires admin session."""
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return JSONResponse(status_code=401, content={"error": "Admin authentication required"})

    category = get_category_by_slug(slug)
    if not category:
        return JSONResponse(status_code=404, content={"error": "Category not found"})

    applications, stats = _fetch_live_data_for_category(category)

    resp = JSONResponse({
        "category": category,
        "stats": stats,
        "applications": applications
    })
    sm.save_session(resp, session_id)
    return resp


@router.get("/api/application/{asset_id}/{trace_id}")
def get_application_presigned_url(request: Request, asset_id: str, trace_id: str):
    """Return presigned URL for a completed application. Requires admin session."""
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return JSONResponse(status_code=401, content={"error": "Admin authentication required"})

    try:
        client = RestClient(base_url=settings.PLATFORM_BASE_URL, agent_client=get_agent_client())
        data = client.get(f"/invokeasset/governance/{asset_id}/{trace_id}")

        output = data.get("response", {}).get("output", [])
        presigned_url = output[0].get("presigned_url") if output else None

        if not presigned_url:
            return JSONResponse(status_code=404, content={"error": "Presigned URL not available"})

        resp = JSONResponse({"presigned_url": presigned_url})
        sm.save_session(resp, session_id)
        return resp

    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else 500
        logger.error(f"HTTP error fetching presigned URL: {e}")
        return JSONResponse(status_code=status, content={"error": "Platform API error"})
    except Exception as e:
        logger.error(f"Error fetching presigned URL asset={asset_id} trace={trace_id}: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to fetch presigned URL"})


@router.get("/admin/api/request-logs")
def get_request_logs_api(request: Request, request_type: str = None):
    """Return request logs, optionally filtered by type. Requires admin session."""
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return JSONResponse(status_code=401, content={"error": "Admin authentication required"})

    from app.services.request_log_service import get_request_logs, get_request_log_stats
    logs = get_request_logs(request_type=request_type)
    stats = get_request_log_stats()

    # Serialize datetime objects to strings
    for log in logs:
        if log.get("created_at") and hasattr(log["created_at"], "isoformat"):
            log["created_at"] = log["created_at"].isoformat()

    resp = JSONResponse({"logs": logs, "stats": stats})
    sm.save_session(resp, session_id)
    return resp

