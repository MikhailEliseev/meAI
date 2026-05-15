"""
Structured logging configuration for AIM Agency

Provides production-grade JSON logging with structlog.
"""

import structlog
import logging
from pathlib import Path
from typing import Optional


def configure_logging(environment: str = "production", log_level: str = "INFO") -> structlog.BoundLogger:
    """
    Configure structured logging for production

    Args:
        environment: Environment name (production, development)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured structlog logger
    """

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Determine log level
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=level,
        handlers=[
            logging.FileHandler(log_dir / "app.log"),
            logging.StreamHandler(),
        ]
    )

    # Configure structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Add appropriate renderer based on environment
    if environment == "production":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logger = structlog.get_logger()
    logger.info(
        "logging_configured",
        environment=environment,
        log_level=log_level,
        log_dir=str(log_dir)
    )

    return logger


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a logger instance

    Args:
        name: Optional logger name for context

    Returns:
        Configured structlog logger
    """
    logger = structlog.get_logger()
    if name:
        logger = logger.bind(logger_name=name)
    return logger
