"""
Admin routes — separate login session from regular users.

- GET  /admin/login  → serve admin login page
- POST /admin/login  → validate admin credentials, set admin_logged_in
- POST /admin/logout → clear admin session, redirect to /admin/login
- GET  /admin        → dashboard (requires admin_logged_in)
- GET  /admin/api/*  → JSON endpoints (requires admin_logged_in)
"""

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.core.dependencies import get_session_manager
from app.core.logger import get_logger
from app.data.demo_data import APPLICATIONS, ADMIN_USERS

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

        if username in ADMIN_USERS and ADMIN_USERS[username]['password'] == password:
            session['admin_logged_in'] = True
            session['admin_username'] = ADMIN_USERS[username]['display_name']
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

@router.get("", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    """Serve the admin dashboard. Requires admin session."""
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return redirect

    stats = _get_stats()
    tmpl = templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "app_name": settings.APP_NAME,
            "theme_css": f"css/style_{settings.APP_THEME}.css",
            "stats": stats,
            "applications": APPLICATIONS,
            "username": session.get('admin_username', 'Admin')
        }
    )
    sm.save_session(tmpl, session_id)
    return tmpl


@router.get("/api/stats")
def get_stats(request: Request):
    """Return dashboard stats as JSON. Requires admin session."""
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return JSONResponse(status_code=401, content={"error": "Admin authentication required"})
    resp = JSONResponse(_get_stats())
    sm.save_session(resp, session_id)
    return resp


@router.get("/api/applications")
def get_applications(request: Request):
    """Return all applications as JSON. Requires admin session."""
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return JSONResponse(status_code=401, content={"error": "Admin authentication required"})
    resp = JSONResponse({"applications": APPLICATIONS})
    sm.save_session(resp, session_id)
    return resp
