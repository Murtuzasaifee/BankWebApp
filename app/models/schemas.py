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



class LoanResponse(BaseModel):
    success: bool
    message: str
    trace_id: Optional[str] = None


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
