"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel
from typing import Optional, List, Any


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str


class AuthStatusResponse(BaseModel):
    logged_in: bool
    username: Optional[str] = None
    user_data: Optional[dict] = None


class ChatRequest(BaseModel):
    history: Optional[List[dict]] = None
    last_query: str


class ChatResponse(BaseModel):
    response: str
    agent_name: Optional[str] = None
    conversation_id: Optional[str] = None
    error: Optional[str] = None


class LoanRequest(BaseModel):
    loan_type: str
    files_count: int = 0
    comments: Optional[str] = ""


class SavingsAccountRequest(BaseModel):
    input_bucket_path: str
    country_code: str
    current_date: str
    output_bucket_path: str
    report_file_type: str
    use_case: str
    process: str
    secondary_language: str = "NA"



class LoanResponse(BaseModel):
    success: bool
    message: str
    trace_id: Optional[str] = None


class SavingsAccountResponse(BaseModel):
    success: bool
    message: str
    trace_id: Optional[str] = None
    documents_count: int = 0


class RequestLogEntry(BaseModel):
    id: int
    user_id: Optional[str] = None
    request_type: str
    account_type: Optional[str] = None
    trace_id: Optional[str] = None
    document_count: int = 0
    status: str
    ip_address: Optional[str] = None
    created_at: str


class HealthResponse(BaseModel):
    status: str
    agent_configured: bool
    asset_version_id: str


class ConfigResponse(BaseModel):
    asset_version_id: str
    agent_name: str
    conversation_name: str
    query_timeout: int
    conversation_count: int


# Admin schemas
class ApplicationSummary(BaseModel):
    application_id: str
    applicant_name: str
    submission_date: str
    status: str
    application_type: str
    application_html_url: str


class DashboardStats(BaseModel):
    pending: int
    in_progress: int
    completed: int
    total: int
