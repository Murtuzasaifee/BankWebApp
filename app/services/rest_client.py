"""
Reusable REST client.

Usage:
    client = RestClient(base_url=settings.PLATFORM_BASE_URL, agent_client=agent_client)
    data = client.get("/resource/123")
    data = client.post("/resource", body={"key": "value"})
"""

import requests
from app.core.logger import get_logger

logger = get_logger()


class RestClient:
    def __init__(self, base_url: str, agent_client):
        self.base_url = base_url.rstrip("/")
        self.agent_client = agent_client

    def get(self, path: str, params: dict = None, extra_headers: dict = None) -> dict:
        response = self._request("GET", path, params=params, extra_headers=extra_headers)
        if response.status_code == 401:
            logger.warning("Token expired, refreshing and retrying...")
            self.agent_client.refresh_access_token()
            response = self._request("GET", path, params=params, extra_headers=extra_headers)
        response.raise_for_status()
        return response.json()

    def post(self, path: str, body: dict = None, extra_headers: dict = None) -> dict:
        response = self._request("POST", path, json=body or {}, extra_headers=extra_headers)
        if response.status_code == 401:
            logger.warning("Token expired, refreshing and retrying...")
            self.agent_client.refresh_access_token()
            response = self._request("POST", path, json=body or {}, extra_headers=extra_headers)
        response.raise_for_status()
        return response.json()

    def _request(self, method: str, path: str, extra_headers: dict = None, **kwargs) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = self.agent_client.get_headers()
        if extra_headers:
            headers.update(extra_headers)
        return requests.request(method, url, headers=headers, timeout=30, **kwargs)
