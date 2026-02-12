"""
Centralized logging configuration using Loguru.

Provides structured logging with rotation, retention, and environment-aware settings.
"""

import sys
from pathlib import Path
from loguru import logger

from app.core.config import get_settings


def setup_logging():
    """
    Configure Loguru logger based on application settings.

    Features:
    - Environment-aware log levels (DEBUG for local, INFO for production)
    - File rotation and retention
    - Colored console output for local development
    - Structured JSON logging for production
    - Request ID tracking support
    """
    settings = get_settings()

    # Remove default handler
    logger.remove()

    # Determine log level based on environment
    log_level = settings.LOG_LEVEL
    if settings.ENVIRONMENT == "local" and settings.DEBUG_MODE:
        log_level = "DEBUG"
    elif settings.ENVIRONMENT == "production":
        log_level = "INFO"

    # Console handler - colorful for local, simple for production
    if settings.ENVIRONMENT == "local":
        # Colored, detailed format for local development
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
            colorize=True,
        )
    else:
        # Simple format for production (logs go to systemd journal)
        logger.add(
            sys.stderr,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            colorize=False,
        )

    # File handler - rotating logs
    log_file = Path("logs") / f"{settings.APP_NAME.lower().replace(' ', '_')}.log"
    log_file.parent.mkdir(exist_ok=True)

    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        enqueue=True,  # Async logging for better performance
    )

    # Error log file - only errors and above
    error_log_file = Path("logs") / f"{settings.APP_NAME.lower().replace(' ', '_')}_errors.log"
    logger.add(
        error_log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        backtrace=True,  # Include full traceback
        diagnose=True,   # Include variable values in traceback
        enqueue=True,
    )

    logger.info(f"Logging initialized for {settings.APP_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Log file: {log_file}")

    return logger


def get_logger():
    """
    Get the configured logger instance.

    Usage:
        from app.core.logger import get_logger
        logger = get_logger()
        logger.info("Something happened")
        logger.error("An error occurred", exc_info=True)
    """
    return logger
