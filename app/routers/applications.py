"""
Application submission routes — Loan and Stock Trading Account Opening.

Both share the same platform invocation pattern via helper functions.
The asset ID comes from categories.py; only the payload and transport differ:
  - Loan:         JSON POST  via _invoke_asset()
  - Stock Account: multipart POST via _invoke_asset_multipart()
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, File, Form, Request, Response, UploadFile
from fastapi.responses import JSONResponse

from app.models.schemas import LoanRequest
from app.core.config import get_settings
from app.core.dependencies import get_agent_client, get_session_manager
from app.core.logger import get_logger
from app.services.rest_client import RestClient
from app.services.category_service import get_asset_id
from app.services.request_log_service import log_request

router = APIRouter()
logger = get_logger()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _asset_id_for(category_slug: str, subcategory_slug: str) -> Optional[str]:
    """Return the asset_id for the given category/subcategory slugs, or None if unconfigured."""
    return get_asset_id(category_slug, subcategory_slug)


def _invoke_asset(asset_id: str, payload: dict, settings, agent_client) -> str:
    """
    Invoke a platform asset with a JSON body and return the trace_id.

    Raises:
        ValueError: if the response contains no trace_id.
        requests.HTTPError: on non-2xx platform responses.
    """
    client = RestClient(base_url=settings.PLATFORM_BASE_URL, agent_client=agent_client)
    logger.info(f"[Asset Invoke] asset_id={asset_id} payload={payload}")
    response = client.post(f"/invokeasset/{asset_id}/usecase", body=payload)
    trace_id = response.get("trace_id") or response.get("traceId") or response.get("id")
    if not trace_id:
        raise ValueError(f"No trace_id in response: {response}")
    logger.info(f"[Asset Invoke] trace_id={trace_id}")
    return trace_id


def _invoke_asset_multipart(
    asset_id: str,
    files: list,
    settings,
    agent_client,
) -> str:
    """
    Invoke a platform asset with uploaded files as multipart/form-data and return the trace_id.

    Args:
        files: List of (field_name, (filename, bytes, content_type)) tuples.

    Raises:
        ValueError: if the response contains no trace_id.
        requests.HTTPError: on non-2xx platform responses.
    """
    client = RestClient(base_url=settings.PLATFORM_BASE_URL, agent_client=agent_client)
    file_names = [f[1][0] for f in files]
    logger.info(f"[Asset Invoke Multipart] asset_id={asset_id} files={file_names}")
    response = client.post_multipart(f"/invokeasset/{asset_id}/usecase", files=files)
    trace_id = response.get("trace_id") or response.get("traceId") or response.get("id")
    if not trace_id:
        raise ValueError(f"No trace_id in response: {response}")
    logger.info(f"[Asset Invoke Multipart] trace_id={trace_id}")
    return trace_id


# ---------------------------------------------------------------------------
# Loan Application
# ---------------------------------------------------------------------------

@router.post("/submit-loan")
def submit_loan(body: LoanRequest, request: Request, response: Response):
    """
    Invoke the loan due-diligence agent and return the trace_id as Application ID.
    """
    try:
        settings = get_settings()
        agent_client = get_agent_client()
        sm = get_session_manager()
        session_id, session = sm.get_session(request)

        if not body.loan_type:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Loan type is required"},
            )

        logger.info(f"[Loan Application] Type: {body.loan_type}, Files: {body.files_count}")

        asset_id = _asset_id_for("loan-application", "personal-loan")
        if not asset_id:
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Loan application asset is not configured"},
            )

        payload = {
            "input_bucket_path": "loan_due_diligence/p1",
            "country_iso_code": "UAE",
            "current_date": datetime.now().strftime("%d/%m/%Y"),
            "output_bucket_path": "loan_due_diligence/output",
            "file_type": "html",
            "Use_Case": "LOAN_APPLICATION",
        }

        trace_id = _invoke_asset(asset_id, payload, settings, agent_client)
        user_id = session.get("user_id") if session else None
        try:
            log_request(
                request_type="loan-application",
                user_id=user_id,
                account_type=body.loan_type,
                trace_id=trace_id,
                document_count=body.files_count,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                comments=body.comments,
            )
        except Exception as log_err:
            logger.warning(f"[Loan Application] Failed to log request: {log_err}")
        sm.save_session(response, session_id)
        return {"success": True, "trace_id": trace_id, "message": "Loan application submitted successfully"}

    except ValueError as e:
        logger.error(f"[Loan Application] No trace_id: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Loan agent did not return an application ID"},
        )
    except Exception as e:
        logger.error(f"[Loan Application] Submission failed: {e}")
        logger.exception("[Loan Application] Exception details")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "An error occurred while processing your loan application"},
        )


# ---------------------------------------------------------------------------
# Stock Trading Account Opening
# ---------------------------------------------------------------------------

@router.post("/submit-stock-account")
async def submit_stock_account(
    request: Request,
    response: Response,
    files: List[UploadFile] = File(...),
):
    """
    Accept PDF uploads as multipart form data, invoke the account-opening agent,
    and return the trace_id as Application ID.
    """
    try:
        settings = get_settings()
        agent_client = get_agent_client()
        sm = get_session_manager()
        session_id, session = sm.get_session(request)

        if not files:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "At least one document is required"},
            )

        logger.info(f"[Stock Account] Files: {len(files)}")

        asset_id = _asset_id_for("account-opening", "demat-account")
        if not asset_id:
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Account opening asset is not configured"},
            )

        # Read each uploaded PDF and prepare multipart tuples
        multipart_files = []
        for f in files:
            content = await f.read()
            multipart_files.append(
                ("DematForm", (f.filename, content, f.content_type or "application/pdf"))
            )

        trace_id = _invoke_asset_multipart(asset_id, multipart_files, settings, agent_client)
        user_id = session.get("user_id") if session else None
        try:
            log_request(
                request_type="stock-account",
                user_id=user_id,
                account_type="Demat Account",
                trace_id=trace_id,
                document_count=len(files),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        except Exception as log_err:
            logger.warning(f"[Stock Account] Failed to log request: {log_err}")
        sm.save_session(response, session_id)
        return {
            "success": True,
            "trace_id": trace_id,
            "message": "Stock trading account application submitted successfully",
        }

    except ValueError as e:
        logger.error(f"[Stock Account] No trace_id: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Account opening agent did not return an application ID"},
        )
    except Exception as e:
        logger.error(f"[Stock Account] Submission failed: {e}")
        logger.exception("[Stock Account] Exception details")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "An error occurred while processing your stock account application"},
        )


# ---------------------------------------------------------------------------
# Savings / Current Account Opening
# ---------------------------------------------------------------------------

@router.post("/submit-savings-account")
async def submit_savings_account(
    request: Request,
    response: Response,
    account_type: str = Form("Savings Account"),
    comments: str = Form(""),
    files: List[UploadFile] = File(...),
):
    """
    Accept PDF uploads as multipart form data, invoke the savings account-opening agent,
    and return the trace_id as Application ID. Available to all users (no login required).
    """
    try:
        settings = get_settings()
        agent_client = get_agent_client()
        sm = get_session_manager()
        session_id, session = sm.get_session(request)

        if not files:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "At least one document is required"},
            )

        logger.info(f"[Savings Account] Type: {account_type}, Files: {len(files)}")

        asset_id = _asset_id_for("account-opening", "savings-account")
        if not asset_id:
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Savings account opening asset is not configured"},
            )

        # Read each uploaded PDF and prepare multipart tuples
        multipart_files = []
        for f in files:
            content = await f.read()
            multipart_files.append(
                ("SavingsForm", (f.filename, content, f.content_type or "application/pdf"))
            )

        trace_id = _invoke_asset_multipart(asset_id, multipart_files, settings, agent_client)
        user_id = session.get("user_id") if session else None
        try:
            log_request(
                request_type="savings-account",
                user_id=user_id,
                account_type=account_type,
                trace_id=trace_id,
                document_count=len(files),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                comments=comments or None,
            )
        except Exception as log_err:
            logger.warning(f"[Savings Account] Failed to log request: {log_err}")
        sm.save_session(response, session_id)
        return {
            "success": True,
            "trace_id": trace_id,
            "documents_count": len(files),
            "message": "Savings account application submitted successfully",
        }

    except ValueError as e:
        logger.error(f"[Savings Account] No trace_id: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Account opening agent did not return an application ID"},
        )
    except Exception as e:
        logger.error(f"[Savings Account] Submission failed: {e}")
        logger.exception("[Savings Account] Exception details")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "An error occurred while processing your account application"},
        )
