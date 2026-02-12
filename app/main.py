#!/usr/bin/env python3
"""
FastAPI web server for Good Bank Chat Application.

This server:
1. Serves the HTML chat interface
2. Handles chat requests from the UI
3. Uses AgentPlatformClient to communicate with the AI agent platform
4. Manages conversations per session
"""

import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, validate_config
from app.dependencies import get_agent_client
from app.routers import pages, auth, chat, loan, health

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # Startup: validate config and initialize agent client
    is_valid, error_msg = validate_config(settings)
    if not is_valid:
        print("=" * 80)
        print("CONFIGURATION ERROR")
        print("=" * 80)
        print(f"Error: {error_msg}")
        print()
        print("Please update .env with the required values.")
        print("See .env.example for the template.")
        print("=" * 80)
        sys.exit(1)

    # Initialize agent client eagerly (triggers token refresh)
    get_agent_client()

    print("=" * 80)
    print("Good Bank Chat Server Starting...")
    print("=" * 80)
    print(f"Asset Version ID: {settings.ASSET_VERSION_ID}")
    print(f"Agent Name: {settings.AGENT_NAME}")
    print(f"Conversation Name: {settings.CONVERSATION_NAME}")
    print(f"Query Timeout: {settings.QUERY_TIMEOUT}s")
    print(f"Server: {settings.SERVER_HOST}:{settings.SERVER_PORT}")
    print(f"Debug Mode: {settings.DEBUG_MODE}")
    print("=" * 80)
    print()

    yield

    # Shutdown
    print("Good Bank Chat Server Shutting Down...")


app = FastAPI(
    title="Good Bank Chat Application",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Routers
app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(loan.router)
app.include_router(health.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG_MODE,
    )
