import logging
import sys
from logging.handlers import TimedRotatingFileHandler


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        file_handler = TimedRotatingFileHandler(
            "app.log", when="midnight", interval=1
        )
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y%m%d"

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger

