"""
Loan application route - handles loan submission and triggers loan processing agent.
"""

import time
import traceback

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.models.schemas import LoanRequest
from app.core.config import get_settings
from app.data.demo_data import USERS
from app.core.dependencies import get_agent_client, get_session_manager
from app.core.logger import get_logger
from app.services.rest_client import RestClient

router = APIRouter()
logger = get_logger()


@router.post("/submit-loan")
def submit_loan(body: LoanRequest, request: Request, response: Response):
    """
    Handle loan application submission and trigger loan processing agent.

    Generates a reference number and triggers the loan agent for backend processing.
    """
    try:
        settings = get_settings()
        agent_client = get_agent_client()
        sm = get_session_manager()
        session_id, session = sm.get_session(request)

        loan_type = body.loan_type
        files_count = body.files_count
        comments = body.comments

        if not loan_type:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Loan type is required"},
            )

        logger.info(f"[Loan Application] Type: {loan_type}, Files: {files_count}")

        # Generate simple reference number
        reference_number = f"LN-{str(int(time.time()))[-8:]}"
        logger.info(f"[Loan Application] Generated Reference Number: {reference_number}")

        # Trigger loan processing agent (for backend processing only)
        agent_response = None
        trace_id = None

        try:
            client = RestClient(base_url=settings.PLATFORM_BASE_URL, agent_client=agent_client)

            # Step 1: Validate asset (non-fatal)
            try:
                client.get(f"/assets/feature/{settings.LOAN_AGENT_ASSET_ID}/",
                           params={"exclude_mimetype": "true"})
                logger.debug("[Loan Agent] Asset validation successful")
            except Exception as e:
                logger.debug(f"[Loan Agent] Asset validation skipped: {e}")

            # Step 2: Invoke loan agent
            username = session.get('username', 'Guest')
            user_id = USERS.get(username, {}).get('user_id', 'usr001')
            invoke_payload = {"User": user_id}
            logger.info(f"[Loan Agent] Sending payload: {invoke_payload}")

            agent_response = client.post(
                f"/invokeasset/{settings.LOAN_AGENT_ASSET_ID}/usecase",
                body=invoke_payload,
                extra_headers={"app": "magicplatform"}
            )

            logger.info("[Loan Agent] Successfully triggered loan processing agent")
            trace_id = (agent_response.get('trace_id') or
                        agent_response.get('traceId') or
                        agent_response.get('id'))
            if trace_id:
                logger.info(f"[Loan Agent] Received trace_id: {trace_id}")
            else:
                logger.warning(f"[Loan Agent] No trace_id. Response keys: {list(agent_response.keys())}")

        except Exception as agent_error:
            logger.error(f"[Loan Agent] Error triggering agent: {agent_error}")
            logger.exception("[Loan Agent] Exception details")
            agent_response = None
            trace_id = None

        logger.info(f"[Loan Application] Final Reference Number (for customer): {reference_number}")

        sm.save_session(response, session_id)
        return {
            "success": True,
            "reference_number": reference_number,
            "message": "Loan application submitted successfully",
            "agent_triggered": agent_response is not None,
            "trace_id": trace_id,
            "agent_response": agent_response,
        }

    except Exception as e:
        logger.error(f"Error in loan submission endpoint: {e}")
        logger.exception("Loan submission endpoint exception")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "An error occurred while processing your loan application"},
        )
