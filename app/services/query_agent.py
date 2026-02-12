"""
AI Agent Platform Client Library

This module provides the AgentPlatformClient class for interacting with the AI agent platform.
It handles authentication, conversation management, and query/response operations.
"""

import requests
import json 
import time
import re
from typing import Optional, Tuple, Dict, Any


class AgentPlatformClient:
    """
    Client for interacting with the AI agent platform.

    This class handles authentication, conversation management, and query/response
    operations with the platform.
    """

    def __init__(self, settings=None, **kwargs):
        """
        Initialize the Agent Platform Client.

        Args:
            settings: A Settings object from app.config (preferred)
            **kwargs: Individual config values (base_url, auth_base, tenant, etc.)
        """
        if settings:
            self.base_url = settings.PLATFORM_BASE_URL
            self.auth_base = settings.AUTH_BASE_URL
            self.tenant = settings.TENANT
            self.api_key = settings.API_KEY
            self.workspace_id = settings.WORKSPACE_ID
            self.username = settings.PLATFORM_USERNAME
            self.password = settings.PLATFORM_PASSWORD
        else:
            self.base_url = kwargs.get('base_url', '')
            self.auth_base = kwargs.get('auth_base', '')
            self.tenant = kwargs.get('tenant', '')
            self.api_key = kwargs.get('api_key', '')
            self.workspace_id = kwargs.get('workspace_id', '')
            self.username = kwargs.get('username', '')
            self.password = kwargs.get('password', '')

        # Token cache
        self.access_token = None
        self.refresh_token = None

        # Authenticate on initialization
        self.refresh_access_token()

    def refresh_access_token(self) -> bool:
        """
        Refresh the access token by making a new authentication request.

        Returns:
            True if token refresh was successful, False otherwise
        """
        try:
            print(f"[{time.strftime('%H:%M:%S')}] Refreshing access token...")

            headers = {
                "apikey": self.api_key,
                "username": self.username,
                "password": self.password,
                "Content-Type": "application/json"
            }

            response = requests.get(
                f"{self.auth_base}/{self.tenant}",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            self.access_token = data.get("access_token") or data.get("accessToken")
            self.refresh_token = data.get("refresh_token") or data.get("refreshToken")

            if self.access_token:
                print(f"[{time.strftime('%H:%M:%S')}] Successfully refreshed access token")
                return True
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Failed to get access token from response")
                return False

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Error refreshing token: {e}")
            return False

    def get_headers(self, accept_type: str = "application/json") -> Dict[str, str]:
        """
        Get request headers with authentication.

        Args:
            accept_type: Accept header type (default: application/json)

        Returns:
            Dictionary of headers
        """
        if not self.access_token:
            self.refresh_access_token()

        return {
            "Accept": accept_type,
            "apikey": self.api_key,
            "authorization": f"Bearer {self.access_token}",
            "refreshtoken": self.refresh_token,
            "x-platform-workspaceid": self.workspace_id,
            "Content-Type": "application/json"
        }

    def create_conversation(
        self,
        asset_version_id: str,
        conversation_name: str = "Quick Chat"
    ) -> Optional[str]:
        """
        Create a new conversation for the given asset.

        Args:
            asset_version_id: The asset version ID to create conversation for
            conversation_name: Name for the conversation (default: "Quick Chat")

        Returns:
            Conversation ID if successful, None otherwise
        """
        try:
            print(f"[{time.strftime('%H:%M:%S')}] Creating new conversation for asset: {asset_version_id}")

            headers = self.get_headers()
            payload = {
                "asset_version_id": asset_version_id,
                "conversation_name": conversation_name
            }

            response = requests.post(
                f"{self.base_url}/genai/conversation/create",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 404:
                error_msg = response.json().get("message", "Unknown error")
                if "Asset not found" in error_msg:
                    raise RuntimeError(
                        f"Asset version ID '{asset_version_id}' not found. "
                        "Please check if the asset exists and is accessible with your credentials."
                    )
                else:
                    raise RuntimeError(f"API Error: {error_msg}")

            response.raise_for_status()

            data = response.json()

            # Try to extract conversation ID from various possible locations
            conv_id = None
            for key in ["conversation_details", "data"]:
                if key in data and data[key]:
                    conv = data[key]
                    conv_id = (
                        conv.get("conversation_id") or
                        conv.get("conversationId") or
                        conv.get("_id") or
                        conv.get("id")
                    )
                    break

            if not conv_id:
                conv_id = data.get("conversation_id") or data.get("conversationId")

            if conv_id:
                print(f"[{time.strftime('%H:%M:%S')}] Conversation created: {conv_id}")
                return conv_id
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Could not extract conversation ID from response")
                print(f"Response: {json.dumps(data, indent=2)}")
                return None

        except requests.HTTPError as e:
            if e.response.status_code == 401:
                print(f"[{time.strftime('%H:%M:%S')}] Received 401, refreshing token and retrying...")
                self.refresh_access_token()
                return self.create_conversation(asset_version_id, conversation_name)
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Error creating conversation: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Response: {e.response.text}")
                return None
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Unexpected error creating conversation: {e}")
            return None

    def clean_agent_response(self, raw_response: str) -> str:
        """
        Clean the agent response by removing streaming artifacts while preserving markdown formatting.

        Args:
            raw_response: Raw response string from the agent

        Returns:
            Cleaned response string with formatting preserved
        """
        if not raw_response:
            return ''

        lines = raw_response.split('\n')
        print(f"Response before cleaning {lines}")
        cleaned_lines = []
        seen_content = set()

        for line in lines:
            original_line = line
            line_stripped = line.strip()

            # Skip streaming status messages (only if entire line matches)
            skip_phrases = [
                'Stream connection established successfully',
                'stream connection established',
                'agent execution inprogress',
                'agent execution in progress',
                'connection established',
            ]

            if any(skip_phrase.lower() == line_stripped.lower() for skip_phrase in skip_phrases):
                continue

            # Skip pure JSON structures (entire line is JSON)
            if (line_stripped.startswith('{') and line_stripped.endswith('}') and
                line_stripped.count('"') > 4):
                continue

            # Skip very short technical lines
            if len(line_stripped) < 3 and not line_stripped:
                continue

            # Skip duplicate lines (but preserve structure)
            line_lower = line_stripped.lower()
            if line_lower and line_lower in seen_content:
                # Still allow empty lines and preserve structure
                if not line_stripped:
                    cleaned_lines.append('')
                continue

            if line_lower:
                seen_content.add(line_lower)

            # Preserve the original line (with indentation) to maintain markdown structure
            cleaned_lines.append(original_line)

        # Join lines preserving newlines (don't join with spaces!)
        cleaned_text = '\n'.join(cleaned_lines)

        # Remove technical artifacts but preserve structure
        cleaned_text = re.sub(r'\{"[^"]*":[^}]*\}', '', cleaned_text)
        cleaned_text = re.sub(r'^data:\s*', '', cleaned_text, flags=re.MULTILINE)
        cleaned_text = re.sub(r'^event:\s*', '', cleaned_text, flags=re.MULTILINE)

        # Remove excessive blank lines (more than 2 consecutive)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

        # Trim leading/trailing whitespace but preserve internal structure
        cleaned_text = cleaned_text.strip()

        return cleaned_text

    def send_query(
        self,
        conversation_id: str,
        query: str,
        timeout: int = 60
    ) -> Tuple[Optional[str], bool]:
        """
        Send a query to the agent and retrieve the response.

        Args:
            conversation_id: The conversation ID to send the query to
            query: The query text to send
            timeout: Request timeout in seconds (default: 60)

        Returns:
            Tuple of (response_text, success_flag)
        """
        try:
            print(f"[{time.strftime('%H:%M:%S')}] Sending query to conversation {conversation_id}")
            print(f"[{time.strftime('%H:%M:%S')}] Query: {query[:100]}...")

            # Use streaming endpoint for real-time response
            headers = self.get_headers(accept_type="text/event-stream")

            payload = {
                "conversation_id": conversation_id,
                "query": query
            }

            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/genai/conversation/addmessage/stream",
                headers=headers,
                json=payload,
                stream=True,
                timeout=timeout
            )

            if response.status_code == 401:
                print(f"[{time.strftime('%H:%M:%S')}] Received 401, refreshing token and retrying...")
                self.refresh_access_token()
                return self.send_query(conversation_id, query, timeout)

            response.raise_for_status()

            # Collect all response chunks
            all_chunks = []
            print(f"[{time.strftime('%H:%M:%S')}] Processing streaming response chunks...")

            for line in response.iter_lines(decode_unicode=True):
                if not line or line.startswith(":"):
                    continue

                if line.startswith("data:"):
                    payload_text = line[5:].strip()
                    if payload_text == "[DONE]":
                        print(f"[{time.strftime('%H:%M:%S')}] Received [DONE] signal")
                        break
                    all_chunks.append(payload_text)

            print(f"[{time.strftime('%H:%M:%S')}] Collected {len(all_chunks)} response chunks")

            # Process chunks to find the final complete response
            final_response = None
            streamed_content = []

            for i, chunk in enumerate(all_chunks):
                try:
                    obj = json.loads(chunk)
                    event_type = obj.get("event")

                    # Priority 1: Check for FINAL_RESPONSE event (contains the complete, clean answer)
                    if event_type == "FINAL_RESPONSE":
                        content_data = obj.get("content", {})
                        if isinstance(content_data, dict) and "response" in content_data:
                            final_response = content_data["response"]
                            # We found the authoritative response, no need to process further
                            break

                    # Priority 2: Accumulate LLM_RESPONSE_STREAM (backup if FINAL_RESPONSE is missing)
                    elif event_type == "LLM_RESPONSE_STREAM":
                        content_str = obj.get("content", "")
                        if content_str:
                            streamed_content.append(content_str)

                except json.JSONDecodeError:
                    continue

            # Determine the return value
            if final_response:
                return_text = final_response
            elif streamed_content:
                # Fallback: Join the streamed tokens if FINAL_RESPONSE wasn't found
                return_text = "".join(streamed_content)
            else:
                return_text = ""

            # Clean the response (removes formatting artifacts if any)
            cleaned_response = self.clean_agent_response(return_text)

            elapsed_time = (time.time() - start_time) * 1000
            print(f"[{time.strftime('%H:%M:%S')}] Response received in {elapsed_time:.1f}ms")
            print(f"[{time.strftime('%H:%M:%S')}] Response length: {len(cleaned_response)} characters")

            return cleaned_response, True

        except requests.HTTPError as e:
            print(f"[{time.strftime('%H:%M:%S')}] HTTP error sending query: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return None, False
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Error sending query: {e}")
            return None, False

    def query_agent(
        self,
        asset_version_id: str,
        query: str,
        conversation_id: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Complete workflow: create/use conversation and send query.

        Args:
            asset_version_id: The asset version ID
            query: The query to send
            conversation_id: Optional existing conversation ID to reuse

        Returns:
            Tuple of (response_text, new_conversation_id)
        """
        # Use existing conversation or create new one
        if not conversation_id:
            conversation_id = self.create_conversation(asset_version_id)
            if not conversation_id:
                return None, None

        # Send query and get response
        response, success = self.send_query(conversation_id, query)

        if success:
            return response, conversation_id
        else:
            return None, conversation_id
