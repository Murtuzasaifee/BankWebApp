"""
FastAPI web server for Banking Chat Application.

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

from app.core.config import get_settings, validate_config
from app.core.dependencies import get_agent_client
from app.core.logger import setup_logging, get_logger
from app.db.connection import init_pool, close_pool
from app.routers import pages, auth, chat, applications, health, admin

# Initialize settings and logging
settings = get_settings()
setup_logging()
logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # Startup: validate config and initialize agent client
    is_valid, error_msg = validate_config(settings)
    if not is_valid:
        logger.critical("=" * 80)
        logger.critical("CONFIGURATION ERROR")
        logger.critical("=" * 80)
        logger.critical(f"Error: {error_msg}")
        logger.critical("Please update .env with the required values.")
        logger.critical("See .env.example for the template.")
        logger.critical("=" * 80)
        sys.exit(1)

    # Initialize agent client eagerly (triggers token refresh)
    get_agent_client()

    # Initialize DB connection pool (no-op if DB_HOST not configured)
    init_pool()

    logger.info("=" * 80)
    logger.info(f"{settings.APP_NAME} Chat Server Starting...")
    logger.info("=" * 80)
    logger.info(f"Asset Version ID: {settings.CHATNOW_ASSET_ID}")
    logger.info(f"Agent Name: {settings.get_agent_name()}")
    logger.info(f"Conversation Name: {settings.get_conversation_name()}")
    logger.info(f"Query Timeout: {settings.QUERY_TIMEOUT}s")
    logger.info(f"Server: {settings.SERVER_HOST}:{settings.SERVER_PORT}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG_MODE}")
    logger.info("=" * 80)

    yield

    # Shutdown
    close_pool()
    logger.info(f"{settings.APP_NAME} Chat Server Shutting Down...")


app = FastAPI(
    title=f"{settings.APP_NAME} Chat Application",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://goodbank.site", 
        "https://www.goodbank.site",
        "http://goodbank.site",
        "http://www.goodbank.site",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
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
app.include_router(applications.router)
app.include_router(health.router)
app.include_router(admin.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG_MODE,
    )
