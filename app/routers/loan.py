"""
Loan application route - handles loan submission and triggers loan processing agent.
"""

import traceback
from datetime import datetime

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.models.schemas import LoanRequest
from app.core.config import get_settings
from app.core.dependencies import get_agent_client, get_session_manager
from app.core.logger import get_logger
from app.services.rest_client import RestClient
from app.data.categories import get_category_by_slug

router = APIRouter()
logger = get_logger()


@router.post("/submit-loan")
def submit_loan(body: LoanRequest, request: Request, response: Response):
    """
    Handle loan application submission and invoke the loan due-diligence agent.

    Returns the platform trace_id as the Application ID shown to the customer.
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

        loan_category = get_category_by_slug("loan-application")
        asset_id = loan_category.get("asset_id") if loan_category else None
        if not asset_id:
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Loan application asset is not configured"},
            )

        invoke_payload = {
            "input_bucket_path": "loan_due_diligence/p1",
            "country_iso_code": "UAE",
            "current_date": datetime.now().strftime("%d/%m/%Y"),
            "output_bucket_path": "loan_due_diligence/output",
            "file_type": "html",
            "Use_Case": "LOAN_APPLICATION",
        }
        logger.info(f"[Loan Agent] Invoking asset {asset_id} with payload: {invoke_payload}")

        client = RestClient(base_url=settings.PLATFORM_BASE_URL, agent_client=agent_client)
        agent_response = client.post(
            f"/invokeasset/{asset_id}/usecase",
            body=invoke_payload,
        )

        trace_id = (agent_response.get('trace_id') or
                    agent_response.get('traceId') or
                    agent_response.get('id'))

        if not trace_id:
            logger.error(f"[Loan Agent] No trace_id in response: {agent_response}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Loan agent did not return an application ID"},
            )

        logger.info(f"[Loan Agent] Application ID (trace_id): {trace_id}")
        sm.save_session(response, session_id)
        return {
            "success": True,
            "trace_id": trace_id,
            "message": "Loan application submitted successfully",
        }

    except Exception as e:
        logger.error(f"[Loan Application] Submission failed: {e}")
        logger.exception("[Loan Application] Exception details")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "An error occurred while processing your loan application"},
        )
