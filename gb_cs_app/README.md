# Good Bank Chat Application

A web-based chat interface integrated with the AI Agent Platform for Good Bank customer support.

## Features

- 🎨 Modern, responsive chat UI
- 🤖 Integration with AI Agent Platform
- 💬 Real-time conversation management
- 🔄 Automatic token refresh
- 📝 Conversation history tracking

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Credentials

Edit `config.py` to set your platform credentials and agent settings:

**Required Settings:**
- `ASSET_VERSION_ID`: The asset version ID for the AI agent
- `API_KEY`: Your platform API key
- `USERNAME`: Platform username
- `PASSWORD`: Platform password
- `WORKSPACE_ID`: Your workspace identifier

**Optional Settings:**
- `AGENT_NAME`: Display name for the agent (default: "Good Bank Support Agent")
- `CONVERSATION_NAME`: Name for conversations (default: "Good Bank Customer Support Chat")
- `QUERY_TIMEOUT`: Query timeout in seconds (default: 60)
- `SERVER_HOST`: Server host (default: "127.0.0.1")
- `SERVER_PORT`: Server port (default: 8000)

### 3. Run the Application

```bash
python app.py
```

The server will start on `http://127.0.0.1:8000`

### 4. Access the Chat Interface

Open your browser and navigate to:
```
http://127.0.0.1:8000
```

## Configuration

All configuration is managed in `config.py`. Simply edit the values directly in the file.

### Platform Credentials (Required)
- `PLATFORM_BASE_URL`: Base URL for the platform API
- `AUTH_BASE_URL`: Base URL for authentication
- `TENANT`: Tenant identifier
- `API_KEY`: API key for authentication
- `WORKSPACE_ID`: Workspace identifier
- `USERNAME`: Username for authentication
- `PASSWORD`: Password for authentication

### Agent Configuration
- `ASSET_VERSION_ID`: Required - The asset version ID for the AI agent
- `AGENT_NAME`: Display name for the agent
- `CONVERSATION_NAME`: Name for conversations
- `QUERY_TIMEOUT`: Query timeout in seconds

### Flask Configuration
- `FLASK_SECRET_KEY`: Flask session secret key
- `SERVER_HOST`: Server host address
- `SERVER_PORT`: Server port number
- `DEBUG_MODE`: Enable/disable debug mode

## Project Structure

```
Good Bank/
├── app.py                 # Flask web server
├── config.py              # Configuration file (credentials & settings)
├── query_agent.py         # AI Agent Platform client
├── templates/
│   └── index.html # Chat UI
├── .gitignore            # Git ignore file
└── README.md             # This file
```

## API Endpoints

### `GET /`
Serves the main chat interface.

### `POST /chat`
Handles chat messages from the UI.

**Request:**
```json
{
  "history": [...],
  "last_query": "user message"
}
```

**Response:**
```json
{
  "response": "agent response",
  "agent_name": "Good Bank Support Agent",
  "conversation_id": "conv-id"
}
```

### `GET /health`
Health check endpoint.

### `GET /config`
Get current configuration (without sensitive data).

## How It Works

1. User enters a message in the chat UI
2. Frontend sends POST request to `/chat` endpoint
3. Flask server uses `AgentPlatformClient` to:
   - Create or retrieve conversation ID
   - Send query to AI Agent Platform
   - Process streaming response
   - Clean and return response
4. Frontend displays the agent's response

## Notes

- The application maintains conversation state per session
- Token refresh is handled automatically
- Conversation IDs are stored in memory (use a database for production)

## Troubleshooting

### "ASSET_VERSION_ID not configured" error
- Make sure you've set `ASSET_VERSION_ID` in `config.py` (line 50)
- The application will validate all required settings on startup

### "Failed to create conversation" error
- Verify your credentials in `config.py`:
  - Check `API_KEY`, `USERNAME`, `PASSWORD`, and `WORKSPACE_ID`
  - Ensure `ASSET_VERSION_ID` is correct and accessible
- Ensure network connectivity to the AI Agent Platform
- Check the console output for detailed error messages

### Connection errors
- Check that the Flask server is running
- Verify the API endpoint URL in the HTML matches the server address
- Check browser console for detailed error messages

