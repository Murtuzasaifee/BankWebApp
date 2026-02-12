"""
Loan application route - handles loan submission and triggers loan processing agent.
"""

import time
import traceback
import requests

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.models.schemas import LoanRequest
from app.core.config import get_settings
from app.data.demo_data import USERS
from app.core.dependencies import get_agent_client, get_session_manager

router = APIRouter()


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

        print(f"[Loan Application] Type: {loan_type}, Files: {files_count}")

        # Generate simple reference number
        reference_number = f"LN-{str(int(time.time()))[-8:]}"
        print(f"[Loan Application] Generated Reference Number: {reference_number}")

        # Trigger loan processing agent (for backend processing only)
        agent_response = None
        trace_id = None

        try:
            access_token = agent_client.access_token

            if access_token:
                # Step 1: Get asset details (optional, for validation)
                asset_url = f"{settings.PLATFORM_BASE_URL.replace('/magicplatform/v1', '')}/magicplatform/v1/assets/feature/{settings.LOAN_AGENT_ASSET_ID}/"
                asset_headers = {
                    'accept': 'application/json',
                    'apikey': settings.API_KEY,
                    'authorization': f'Bearer {access_token}',
                    'x-platform-workspaceid': settings.WORKSPACE_ID,
                }

                asset_response = requests.get(asset_url, headers=asset_headers, params={'exclude_mimetype': 'true'})
                print(f"[Loan Agent] Asset validation status: {asset_response.status_code}")

                # Step 2: Invoke the loan processing agent WITH PAYLOAD
                invoke_url = f"{settings.PLATFORM_BASE_URL.replace('/magicplatform/v1', '')}/magicplatform/v1/invokeasset/{settings.LOAN_AGENT_ASSET_ID}/usecase"
                invoke_headers = {
                    'accept': 'application/json',
                    'apikey': settings.API_KEY,
                    'app': 'magicplatform',
                    'authorization': f'Bearer {access_token}',
                    'x-platform-workspaceid': settings.WORKSPACE_ID,
                    'content-type': 'application/json',
                }

                # Get user_id from session data
                username = session.get('username', 'Guest')
                user_data = USERS.get(username, {})
                user_id = user_data.get('user_id', 'usr001')

                invoke_payload = {"User": user_id}
                print(f"[Loan Agent] Sending payload: {invoke_payload}")

                invoke_response = requests.post(invoke_url, headers=invoke_headers, json=invoke_payload, timeout=30)

                print(f"[Loan Agent] Response Status Code: {invoke_response.status_code}")
                print(f"[Loan Agent] Full Response: {invoke_response.text}")

                # Accept both 200 and 201 as success codes (201 = Created/Invoked)
                if invoke_response.status_code in [200, 201]:
                    agent_response = invoke_response.json()
                    print(f"[Loan Agent] Successfully triggered loan processing agent")
                    print(f"[Loan Agent] Parsed JSON Response: {agent_response}")

                    # Extract trace_id from response (for logging only, not for display)
                    trace_id = agent_response.get('trace_id') or agent_response.get('traceId') or agent_response.get('id')

                    if trace_id:
                        print(f"[Loan Agent] Received trace_id: {trace_id} (stored for backend tracking)")
                    else:
                        print(f"[Loan Agent] WARNING: No trace_id found in response. Response keys: {list(agent_response.keys())}")
                else:
                    print(f"[Loan Agent] Agent invocation failed with status: {invoke_response.status_code}")
                    print(f"[Loan Agent] Error Response: {invoke_response.text}")
            else:
                print("[Loan Agent] No access token available, skipping agent invocation")

        except Exception as agent_error:
            print(f"[Loan Agent] Error triggering agent: {agent_error}")
            traceback.print_exc()
            # Don't fail the loan submission if agent fails

        print(f"[Loan Application] Final Reference Number (for customer): {reference_number}")

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
        print(f"Error in loan submission endpoint: {e}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "An error occurred while processing your loan application"},
        )
