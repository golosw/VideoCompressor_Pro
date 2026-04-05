import logging
import sys

from app.core.config import settings


def setup_logging() -> logging.Logger:
    level = logging.DEBUG if settings.debug else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger("videocompressor")
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False

    return logger


logger = setup_logging()
