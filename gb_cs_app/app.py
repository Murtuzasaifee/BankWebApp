#!/usr/bin/env python3
"""
Flask web server that integrates the AI Agent Platform with the HTML chat UI.

This server:
1. Serves the HTML chat interface
2. Handles chat requests from the UI
3. Uses AgentPlatformClient to communicate with the AI agent platform
4. Manages conversations per session
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from query_agent import AgentPlatformClient
import uuid
import requests
from typing import Optional, Dict
from config import (
    get_agent_config,
    get_flask_config,
    validate_config,
    ASSET_VERSION_ID,
    ASSET_VERSION_ID_LOGGED_IN,
    AGENT_NAME,
    CONVERSATION_NAME,
    QUERY_TIMEOUT,
    LOAN_AGENT_ASSET_ID,
    API_KEY,
    WORKSPACE_ID
)

# Load Flask configuration
flask_config = get_flask_config()
app = Flask(__name__)
app.secret_key = flask_config['secret_key']
CORS(app)

# Initialize the agent client (shared instance)
agent_client = AgentPlatformClient()

# Store conversation IDs per session
# In production, use a proper database or Redis
conversation_store: Dict[str, str] = {}

# Dummy login credentials - Multiple users
USERS = {
    'Mohammed Faisal': {
        'password': 'password',
        'display_name': 'Mohammed Faisal',
        'user_id': 'usr001',  # For agent payload
        'customer_id': 'Good Bank-CUST-459812',
        'account_number': 'Good Bank-SAV-77889900',
        'accounts': [
            {'type': 'Savings Account', 'balance': 8450.00, 'number': 'Good Bank-SAV-••••9900'},
            {'type': 'Debit Card', 'balance': 2340.50, 'number': 'DC-334455'},
            {'type': 'Credit Card', 'balance': 600.00, 'number': 'CC-667788'}
        ],
        'transactions': [
            {'merchant': 'Amazon KSA', 'date': 'Jan 14, 2026', 'time': '18:20', 'type': 'Debit Card', 'amount': -250.00, 'status': 'Failed', 'icon': 'shopping-cart', 'id': 'TXN-3003'},
            {'merchant': 'Carrefour', 'date': 'Jan 14, 2026', 'time': '13:40', 'type': 'Debit Card', 'amount': -200.00, 'status': 'Completed', 'icon': 'shopping-bag', 'id': 'TXN-3002'},
            {'merchant': 'Aramco', 'date': 'Jan 14, 2026', 'time': '09:15', 'type': 'Debit Card', 'amount': -200.00, 'status': 'Completed', 'icon': 'gas-pump', 'id': 'TXN-3001'},
            {'merchant': 'Hunger Station', 'date': 'Jan 13, 2026', 'time': '21:10', 'type': 'Credit Card', 'amount': -900.00, 'status': 'Completed', 'icon': 'cutlery', 'id': 'TXN-3004'},
            {'merchant': 'Noon KSA', 'date': 'Jan 13, 2026', 'time': '22:05', 'type': 'Credit Card', 'amount': -800.00, 'status': 'Failed', 'icon': 'shopping-cart', 'id': 'TXN-3005'}
        ]
    },
    'Ahmed Al Mansouri': {
        'password': 'password',
        'display_name': 'Ahmed Al Mansouri',
        'user_id': 'usr002',  # For agent payload
        'customer_id': 'Good Bank-CUST-289034',
        'account_number': 'Good Bank-SAL-123456789012',
        'accounts': [
            {'type': 'Salary Account', 'balance': 81749.00, 'number': 'Good Bank-SAL-••••9012'},
            {'type': 'Debit Card', 'balance': 15200.00, 'number': 'DC-746406'},
            {'type': 'Savings Account', 'balance': 45000.00, 'number': 'Good Bank-SAV-••••4567'}
        ],
        'transactions': [
            {'merchant': 'ATM Cash Withdrawal', 'date': 'Dec 30, 2025', 'time': '16:45', 'type': 'Debit Card', 'amount': -1000.00, 'status': 'Completed', 'icon': 'money-bill-wave', 'id': 'TXN-8001'},
            {'merchant': 'Fuel Station', 'date': 'Dec 28, 2025', 'time': '08:30', 'type': 'Debit Card', 'amount': -100.00, 'status': 'Completed', 'icon': 'gas-pump', 'id': 'TXN-8002'},
            {'merchant': 'Hunger Station', 'date': 'Dec 27, 2025', 'time': '20:15', 'type': 'Debit Card', 'amount': -70.00, 'status': 'Completed', 'icon': 'utensils', 'id': 'TXN-8003'},
            {'merchant': 'Coffee Shop POS', 'date': 'Dec 26, 2025', 'time': '09:00', 'type': 'Debit Card', 'amount': -18.00, 'status': 'Completed', 'icon': 'coffee', 'id': 'TXN-8004'},
            {'merchant': 'Salary Credit - Asharqia Tech', 'date': 'Dec 25, 2025', 'time': '00:01', 'type': 'Salary', 'amount': 35000.00, 'status': 'Completed', 'icon': 'arrow-down', 'id': 'TXN-8005'}
        ],
        'employer': 'ASHARQIA TECH SOLUTIONS',
        'designation': 'SOFTWARE ENGINEER',
        'monthly_salary': 35000.00,
        'emirates_id': '784-123-1234567-1',
        'mobile': '+971-50-2847361',
        'address': 'B25, BUILDING NO 18, BUTINA AREA, SHARJAH'
    }
}

DISPLAY_NAME = 'User'

# Load agent configuration
agent_config = get_agent_config()


def get_or_create_conversation(session_id: str, asset_version_id: Optional[str] = None) -> Optional[str]:
    """
    Get existing conversation ID for session or create a new one.
    
    Args:
        session_id: Unique session identifier
        asset_version_id: Asset version ID to use (defaults to ASSET_VERSION_ID)
        
    Returns:
        Conversation ID or None if creation fails
    """
    # Use provided asset_version_id or default
    if asset_version_id is None:
        asset_version_id = ASSET_VERSION_ID
    
    # Check if we have an existing conversation for this session
    # If user logged in/out, we need to create a new conversation
    conversation_key = f"{session_id}_{asset_version_id}"
    if conversation_key in conversation_store:
        return conversation_store[conversation_key]
    
    # Create new conversation
    if not asset_version_id:
        print("⚠️  Warning: ASSET_VERSION_ID not set. Cannot create conversation.")
        return None
    
    conversation_id = agent_client.create_conversation(
        asset_version_id=asset_version_id,
        conversation_name=CONVERSATION_NAME
    )
    
    if conversation_id:
        conversation_store[conversation_key] = conversation_id
        print(f"✅ Created new conversation {conversation_id} for session {session_id} with asset {asset_version_id}")
    
    return conversation_id


@app.route('/')
def index():
    """Serve the main chat interface."""
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    """
    Handle user login.
    
    Expected request body:
    {
        "username": "Mohammed Faisal" or "Ahmed Al Mansouri",
        "password": "password"
    }
    
    Returns:
    {
        "success": true/false,
        "message": "Login message"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        # Check if user exists and password matches
        if username in USERS and USERS[username]['password'] == password:
            session['logged_in'] = True
            session['username'] = username
            session['user_data'] = USERS[username]
            
            # Clear existing conversation when logging in to use new asset ID
            if 'session_id' in session:
                session_id = session['session_id']
                # Remove old conversation entries for this session
                keys_to_remove = [k for k in conversation_store.keys() if k.startswith(f"{session_id}_")]
                for key in keys_to_remove:
                    del conversation_store[key]
            
            return jsonify({
                "success": True,
                "message": "Login successful"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Invalid username or password"
            }), 401
            
    except Exception as e:
        print(f"❌ Error in login endpoint: {e}")
        return jsonify({
            "success": False,
            "message": "An error occurred during login"
        }), 500


@app.route('/logout', methods=['POST'])
def logout():
    """
    Handle user logout.
    
    Returns:
    {
        "success": true,
        "message": "Logout message"
    }
    """
    try:
        # Clear existing conversation when logging out to use default asset ID
        if 'session_id' in session:
            session_id = session['session_id']
            # Remove old conversation entries for this session
            keys_to_remove = [k for k in conversation_store.keys() if k.startswith(f"{session_id}_")]
            for key in keys_to_remove:
                del conversation_store[key]
        
        session.pop('logged_in', None)
        session.pop('username', None)
        
        return jsonify({
            "success": True,
            "message": "Logout successful"
        })
        
    except Exception as e:
        print(f"❌ Error in logout endpoint: {e}")
        return jsonify({
            "success": False,
            "message": "An error occurred during logout"
        }), 500


@app.route('/auth/status', methods=['GET'])
def auth_status():
    """
    Get current authentication status.
    
    Returns:
    {
        "logged_in": true/false,
        "username": "username or null",
        "user_data": {...}
    }
    """
    logged_in = session.get('logged_in', False)
    username = session.get('username', None)
    user_data = session.get('user_data', None)
    
    return jsonify({
        "logged_in": logged_in,
        "username": username,
        "user_data": user_data
    })


@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle chat messages from the UI.
    
    Expected request body:
    {
        "history": [...],  # Optional conversation history
        "last_query": "user message"
    }
    
    Returns:
    {
        "response": "agent response text",
        "agent_name": "Agent Name",
        "ticket_id": "optional ticket ID"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No data provided",
                "response": "I'm sorry, I didn't receive your message. Please try again."
            }), 400
        
        query = data.get('last_query', '').strip()
        
        if not query:
            return jsonify({
                "error": "Empty query",
                "response": "Please enter a message."
            }), 400
        
        # Get or create session ID
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        session_id = session['session_id']
        
        # Determine which asset version ID to use based on login status
        is_logged_in = session.get('logged_in', False)
        asset_version_id = ASSET_VERSION_ID_LOGGED_IN if is_logged_in else ASSET_VERSION_ID
        
        # Get or create conversation with appropriate asset ID
        conversation_id = get_or_create_conversation(session_id, asset_version_id)
        
        if not conversation_id:
            return jsonify({
                "error": "Failed to create conversation",
                "response": "I'm sorry, I'm having trouble starting a conversation. Please check the configuration."
            }), 500
        
        print(f"[Chat] Session: {session_id}, Conversation: {conversation_id}, Query: {query[:100]}...")
        
        # Send query to agent
        response_text, success = agent_client.send_query(
            conversation_id=conversation_id,
            query=query,
            timeout=QUERY_TIMEOUT
        )
        
        if not success or not response_text:
            return jsonify({
                "error": "Failed to get response from agent",
                "response": "I'm sorry, I'm having trouble processing your request. Please try again later."
            }), 500
        
        # Return response in expected format
        return jsonify({
            "response": response_text,
            "agent_name": AGENT_NAME,
            "conversation_id": conversation_id
        })
        
    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "response": "I'm sorry, an unexpected error occurred. Please try again."
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "agent_configured": agent_client.access_token is not None,
        "asset_version_id": ASSET_VERSION_ID if ASSET_VERSION_ID else "not configured"
    })


@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration (without sensitive data)."""
    return jsonify({
        "asset_version_id": ASSET_VERSION_ID if ASSET_VERSION_ID else "not configured",
        "agent_name": AGENT_NAME,
        "conversation_name": CONVERSATION_NAME,
        "query_timeout": QUERY_TIMEOUT,
        "conversation_count": len(conversation_store)
    })


@app.route('/submit-loan', methods=['POST'])
def submit_loan():
    """
    Handle loan application submission and trigger loan processing agent.
    
    Expected request body:
    {
        "loan_type": "Personal Loan",
        "files_count": 3,
        "comments": "Optional comments"
    }
    
    Returns:
    {
        "success": true/false,
        "reference_number": "LN-12345678",
        "message": "Status message",
        "agent_response": "Agent processing result (optional)"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
        
        loan_type = data.get('loan_type', '')
        files_count = data.get('files_count', 0)
        comments = data.get('comments', '')
        
        if not loan_type:
            return jsonify({
                "success": False,
                "message": "Loan type is required"
            }), 400
        
        print(f"[Loan Application] Type: {loan_type}, Files: {files_count}")
        
        # Generate simple reference number (NOT using trace_id from agent response)
        import time
        reference_number = f"LN-{str(int(time.time()))[-8:]}"
        print(f"[Loan Application] Generated Reference Number: {reference_number}")
        
        # Trigger loan processing agent (for backend processing only)
        agent_response = None
        trace_id = None
        
        try:
            # Get access token from agent_client
            access_token = agent_client.access_token
            
            if access_token:
                # Step 1: Get asset details (optional, for validation)
                asset_url = f"https://api.intellectseecstag.com/magicplatform/v1/assets/feature/{LOAN_AGENT_ASSET_ID}/"
                asset_headers = {
                    'accept': 'application/json',
                    'apikey': API_KEY,
                    'authorization': f'Bearer {access_token}',
                    'x-platform-workspaceid': WORKSPACE_ID
                }
                
                asset_response = requests.get(asset_url, headers=asset_headers, params={'exclude_mimetype': 'true'})
                print(f"[Loan Agent] Asset validation status: {asset_response.status_code}")
                
                # Step 2: Invoke the loan processing agent WITH PAYLOAD
                invoke_url = f"https://api.intellectseecstag.com/magicplatform/v1/invokeasset/{LOAN_AGENT_ASSET_ID}/usecase"
                invoke_headers = {
                    'accept': 'application/json',
                    'apikey': API_KEY,
                    'app': 'magicplatform',
                    'authorization': f'Bearer {access_token}',
                    'x-platform-workspaceid': WORKSPACE_ID,
                    'content-type': 'application/json'
                }
                
                # Prepare payload with user information
                # Get user_id from session data
                username = session.get('username', 'Guest')
                user_data = USERS.get(username, {})
                user_id = user_data.get('user_id', 'usr001')  # Default to usr001 if not found
                
                invoke_payload = {
                    "User": user_id
                }
                
                print(f"[Loan Agent] Sending payload: {invoke_payload}")
                
                # POST request with payload
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
            import traceback
            traceback.print_exc()
            # Don't fail the loan submission if agent fails
        
        print(f"[Loan Application] Final Reference Number (for customer): {reference_number}")
        
        # Return success response
        return jsonify({
            "success": True,
            "reference_number": reference_number,
            "message": "Loan application submitted successfully",
            "agent_triggered": agent_response is not None,
            "trace_id": trace_id,
            "agent_response": agent_response
        })
        
    except Exception as e:
        print(f"❌ Error in loan submission endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": "An error occurred while processing your loan application"
        }), 500


if __name__ == '__main__':
    # Validate configuration
    is_valid, error_msg = validate_config()
    if not is_valid:
        print("=" * 80)
        print("❌ CONFIGURATION ERROR")
        print("=" * 80)
        print(f"Error: {error_msg}")
        print()
        print("Please update config.py with the required values:")
        print("  - ASSET_VERSION_ID (required) - line 50")
        print("  - API_KEY (required) - line 32")
        print("  - USERNAME (required) - line 39")
        print("  - PASSWORD (required) - line 42")
        print("  - WORKSPACE_ID (required) - line 35")
        print("=" * 80)
        exit(1)
    
    print("=" * 80)
    print("Good Bank Chat Server Starting...")
    print("=" * 80)
    print(f"Asset Version ID: {ASSET_VERSION_ID}")
    print(f"Agent Name: {AGENT_NAME}")
    print(f"Conversation Name: {CONVERSATION_NAME}")
    print(f"Query Timeout: {QUERY_TIMEOUT}s")
    print(f"Server: {flask_config['host']}:{flask_config['port']}")
    print(f"Debug Mode: {flask_config['debug']}")
    print("=" * 80)
    print()
    
    # Run the Flask app
    app.run(
        host=flask_config['host'],
        port=flask_config['port'],
        debug=flask_config['debug']
    )

