import sys
import logging
from src.config import settings

from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record) -> None:
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


logLevel = logging.DEBUG if settings.is_development else logging.INFO


def configure_logging():
    # Remove default loguru handler
    logger.remove()

    # Add loguru handler with custom format
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG" if settings.is_development else "INFO",
    )

    # Intercept all standard logging
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.DEBUG if settings.is_development else logging.INFO)

    # Intercept specific loggers
    for name in ["uvicorn", "uvicorn.access", "uvicorn.error", "sqlalchemy.engine"]:
        logging_logger = logging.getLogger(name)
        logging_logger.handlers = []
        logging_logger.propagate = True
