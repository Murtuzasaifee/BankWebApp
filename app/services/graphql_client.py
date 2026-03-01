"""
Reusable GraphQL client.

Usage:
    client = GraphQLClient(url="https://api.example.com/graphql", agent_client=agent_client)
    data = client.execute({"query": "..."})
"""

import requests
from app.core.logger import get_logger

logger = get_logger()


class GraphQLClient:
    """Thin wrapper around requests for GraphQL endpoints.

    Handles 401 token refresh automatically (single retry).
    """

    def __init__(self, url: str, agent_client):
        self.url = url
        self.agent_client = agent_client

    def execute(self, body: dict) -> dict:
        """POST a GraphQL request body and return the parsed JSON response.

        Retries once after refreshing the token on a 401 response.

        Raises:
            requests.HTTPError: on non-2xx responses (after retry if applicable).
        """
        response = self._post(body)

        if response.status_code == 401:
            logger.warning("Token expired, refreshing and retrying...")
            self.agent_client.refresh_access_token()
            response = self._post(body)

        response.raise_for_status()
        return response.json()

    def _post(self, body: dict) -> requests.Response:
        headers = self.agent_client.get_headers()
        return requests.post(self.url, headers=headers, json=body, timeout=30)
