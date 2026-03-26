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

from app.core.config import get_settings, update_platform_credentials
from app.core.dependencies import get_session_manager, get_agent_client, reset_agent_client
from app.core.logger import get_logger
from app.services.category_service import get_all_categories, get_category_by_slug, get_subcategory_by_slug
from app.services.admin_service import fetch_applications_for_asset, compute_stats, merge_with_db
from app.services.application_service import update_application_status
from app.services.rest_client import RestClient
from app.services.config_service import (
    get_all_cached_asset_ids,
    update_asset_ids,
    reload_asset_ids,
)

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
    Uses limit=50 to retrieve all items (category view is not paginated at API level).
    """
    agent_client = get_agent_client()
    all_applications = []
    for sub in category.get("subcategories", []):
        asset_id = sub.get("asset_id") or ""
        if not asset_id.strip():
            continue
        apps, _ = fetch_applications_for_asset(agent_client, settings, asset_id, page=1, limit=50)
        for app in apps:
            app["subcategory_name"] = sub["name"]
        all_applications.extend(apps)

    all_applications.sort(key=lambda x: x.get("submission_date", ""), reverse=True)
    all_applications = merge_with_db(all_applications)
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


@router.get("/subcategory/{sub_slug}", response_class=HTMLResponse)
def admin_subcategory_detail(request: Request, sub_slug: str):
    """Serve the subcategory detail view with API-level pagination. Requires admin session."""
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return redirect

    subcategory = get_subcategory_by_slug(sub_slug)
    if not subcategory:
        return RedirectResponse(url="/admin", status_code=302)

    tmpl = templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "app_name": settings.APP_NAME,
            "theme_css": f"css/style_{settings.APP_THEME}.css",
            "username": session.get("admin_username", "Admin"),
            "view_mode": "subcategory",
            "subcategory": subcategory,
        }
    )
    sm.save_session(tmpl, session_id)
    return tmpl


@router.get("/api/subcategory/{sub_slug}")
def get_subcategory_data_api(request: Request, sub_slug: str, page: int = 1, limit: int = 10):
    """Return paginated applications and stats for a specific subcategory. Requires admin session."""
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return JSONResponse(status_code=401, content={"error": "Admin authentication required"})

    subcategory = get_subcategory_by_slug(sub_slug)
    if not subcategory:
        return JSONResponse(status_code=404, content={"error": "Subcategory not found"})

    asset_id = subcategory.get("asset_id", "")
    agent_client = get_agent_client()
    applications, pagination = fetch_applications_for_asset(agent_client, settings, asset_id, page=page, limit=limit)
    applications = merge_with_db(applications)
    stats = compute_stats(applications)
    stats["total"] = pagination.get("total_items", stats["total"])

    resp = JSONResponse({
        "subcategory": subcategory,
        "stats": stats,
        "applications": applications,
        "pagination": pagination,
    })
    sm.save_session(resp, session_id)
    return resp


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


@router.post("/api/applications/{application_id}/status")
async def update_application_status_api(
    request: Request,
    application_id: str,
):
    """Approve or reject an application. Requires admin session."""
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return JSONResponse(status_code=401, content={"error": "Admin authentication required"})

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    status = (body.get("status") or "").strip()
    comments = (body.get("comments") or "").strip() or None

    try:
        found = update_application_status(application_id, status, comments)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    if not found:
        return JSONResponse(status_code=404, content={"error": f"Application '{application_id}' not found"})

    logger.info(f"Admin '{session.get('admin_username')}' updated {application_id} -> {status}")
    resp = JSONResponse({"success": True, "application_id": application_id, "status": status})
    sm.save_session(resp, session_id)
    return resp


# ---------------------------------------------------------------------------
# Settings Page
# ---------------------------------------------------------------------------

@router.get("/settings")
def admin_settings(request: Request):
    """Render the admin settings page (asset configuration)."""
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return redirect

    resp = templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "app_name": settings.APP_NAME,
            "theme_css": f"css/style_{settings.APP_THEME}.css",
            "username": session.get("admin_username", "Admin"),
            "view_mode": "settings",
            "workspace_id": settings.WORKSPACE_ID,
            "platform_username": settings.PLATFORM_USERNAME,
            # We don't send the password to the frontend for security.
        },
    )
    sm.save_session(resp, session_id)
    return resp


# ---------------------------------------------------------------------------
# Asset Config API
# ---------------------------------------------------------------------------

@router.get("/api/asset-config")
def get_asset_config(request: Request):
    """Return all cached asset IDs for the admin UI. Requires admin session."""
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return JSONResponse(status_code=401, content={"error": "Admin authentication required"})

    resp = JSONResponse(get_all_cached_asset_ids())
    sm.save_session(resp, session_id)
    return resp


@router.post("/api/asset-config")
async def save_asset_config(request: Request):
    """
    Persist updated asset IDs to app_config and reload the in-memory cache.
    Accepts JSON body:
    {
      "chatnow": "...",
      "intellichat": "...",
      "subcategories": [
        {"key": "savings_account", "value": "..."}, ...
      ]
    }
    Requires admin session.
    """
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return JSONResponse(status_code=401, content={"error": "Admin authentication required"})

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    updates: dict = {}

    if "chatnow" in body:
        updates["chatnow"] = (body["chatnow"] or "").strip()

    if "intellichat" in body:
        updates["intellichat"] = (body["intellichat"] or "").strip()

    for item in body.get("subcategories", []):
        key = (item.get("key") or "").strip()
        value = (item.get("value") or "").strip()
        # Accept any simple key (no dots — that was the old format)
        if key and "." not in key:
            updates[key] = value

    if not updates:
        return JSONResponse(status_code=400, content={"error": "No valid fields to update"})

    try:
        update_asset_ids(updates)
    except Exception as e:
        logger.error(f"Failed to update asset config: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to save asset configuration"})

    resp = JSONResponse({"success": True, "updated": len(updates), "config": get_all_cached_asset_ids()})
    sm.save_session(resp, session_id)
    return resp


@router.post("/api/reload-config")
def reload_config(request: Request):
    """
    Reload the asset ID cache from the DB without changing any values.
    Requires admin session.
    """
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return JSONResponse(status_code=401, content={"error": "Admin authentication required"})

    try:
        reload_asset_ids()
    except Exception as e:
        logger.error(f"Error checking reload task: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

    resp = JSONResponse({"success": True, "config": get_all_cached_asset_ids()})
    sm.save_session(resp, session_id)
    return resp


# ---------------------------------------------------------------------------
# Platform Credentials API
# ---------------------------------------------------------------------------

@router.post("/api/platform-credentials")
async def save_platform_credentials(request: Request):
    """Save platform credentials to .env and memory."""
    session, session_id, sm, redirect = _require_admin(request)
    if redirect:
        return redirect

    try:
        data = await request.json()
        workspace_id = data.get("workspace_id", "").strip()
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        # If they left the password blank, it means they don't want to change it.
        if not password:
            password = settings.PLATFORM_PASSWORD

        success = update_platform_credentials(workspace_id, username, password)
        if not success:
            return JSONResponse({"error": "Failed to save credentials to .env file."}, status_code=500)

        # Force the singleton client to reload its credentials from settings
        reset_agent_client()

        logger.info(f"Admin '{session.get('admin_username')}' updated platform credentials.")
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error saving platform credentials: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
