import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
