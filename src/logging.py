import logging
import sys

from loguru import logger

from src.config import settings


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

    # Console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG" if settings.is_development else "INFO",
    )

    # File handler
    logger.add(
        "logs/app.log",
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG" if settings.is_development else "INFO",
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Intercept specific loggers
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
