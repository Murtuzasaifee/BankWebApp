#!/usr/bin/env python3
"""
Configuration file for Good Bank Chat Application.

This file contains ALL platform credentials, agent settings, and application configuration.
ALL IDs and credentials should be set directly in this file.

REQUIRED CONFIGURATION:
- ASSET_VERSION_ID: Set your asset version ID (line 30)
- API_KEY: Platform API key (line 20)
- USERNAME: Platform username (line 24)
- PASSWORD: Platform password (line 28)
- WORKSPACE_ID: Workspace identifier (line 18)

Simply edit the values below to configure the application.
"""

from typing import Optional, Tuple

# ============================================================================
# AI Agent Platform Credentials
# ============================================================================

# Base URLs
PLATFORM_BASE_URL = 'https://api.intellectseecstag.com/magicplatform/v1'
AUTH_BASE_URL = 'https://api.intellectseecstag.com/accesstoken'

# Platform Authentication
TENANT = 'idxpdemo'

# TODO: Set your API Key here
API_KEY = 'magicplatform.c630A0A1126e4dA3A0D11218625d3331'

# TODO: Set your Workspace ID here
WORKSPACE_ID = 'b60b323e-0ed1-42ae-a7e9-4f386d8e20ac'

# User Credentials
# TODO: Set your username here
USERNAME = 'idxpdemo.murtuza.saifee'

# TODO: Set your password here
PASSWORD = 'Next2Tecom@23'

# ============================================================================
# Agent Configuration
# ============================================================================

# Asset Version ID (ChatNow)
ASSET_VERSION_ID = 'b34ff710-b548-4f0c-9a10-67fce794b632'

# Asset Version ID for logged-in users (IntelliChat)
ASSET_VERSION_ID_LOGGED_IN = '3052533e-4642-4ae0-87d5-75099f013538'

# Onboarding Asset ID (for Onboarding)
LOAN_AGENT_ASSET_ID = '3d588f9e-6e36-4794-8b44-1d4c7d11f6f2'

# Agent Display Name
AGENT_NAME = 'Good Bank Support Agent'

# Conversation Settings
CONVERSATION_NAME = 'Good Bank Customer Support Chat'

# Query Timeout (in seconds)
QUERY_TIMEOUT = 60

# ============================================================================
# Flask Application Configuration
# ============================================================================

# Flask Secret Key (for session management)
FLASK_SECRET_KEY = 'GF3AgTHL2Uc2YJXElZs7tCGl'


# Server Host and Port
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8000

# Debug Mode
DEBUG_MODE = True

# ============================================================================
# Configuration Validation
# ============================================================================

def validate_config() -> Tuple[bool, Optional[str]]:
    """
    Validate that required configuration values are set.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not ASSET_VERSION_ID:
        return False, "ASSET_VERSION_ID is required but not set"
    
    if not API_KEY:
        return False, "API_KEY is required but not set"
    
    if not USERNAME or not PASSWORD:
        return False, "USERNAME and PASSWORD are required but not set"
    
    if not WORKSPACE_ID:
        return False, "WORKSPACE_ID is required but not set"
    
    return True, None


def get_platform_config() -> dict:
    """
    Get platform configuration as a dictionary.
    
    Returns:
        Dictionary with platform configuration
    """
    return {
        'base_url': PLATFORM_BASE_URL,
        'auth_base': AUTH_BASE_URL,
        'tenant': TENANT,
        'api_key': API_KEY,
        'workspace_id': WORKSPACE_ID,
        'username': USERNAME,
        'password': PASSWORD
    }


def get_agent_config() -> dict:
    """
    Get agent configuration as a dictionary.
    
    Returns:
        Dictionary with agent configuration
    """
    return {
        'asset_version_id': ASSET_VERSION_ID,
        'agent_name': AGENT_NAME,
        'conversation_name': CONVERSATION_NAME,
        'query_timeout': QUERY_TIMEOUT
    }




def get_flask_config() -> dict:
    """
    Get Flask application configuration as a dictionary.
    
    Returns:
        Dictionary with Flask configuration
    """
    return {
        'secret_key': FLASK_SECRET_KEY,
        'host': SERVER_HOST,
        'port': SERVER_PORT,
        'debug': DEBUG_MODE
    }


