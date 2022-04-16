import logging
import sys

from app.config import Settings


def configure_logging(name: str) -> logging.Logger:
    logging_format = (
        "[%(asctime)s] - [%(name)s] - [%(levelname)s] - [%(message)s]"
    )
    formatter = logging.Formatter(logging_format)
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    return logger
