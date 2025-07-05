import logging

from config import LOGS_DIR


def setup_logger(name='pdn_admin'):
    """Setup logger for pdn_admin module"""
    logger = logging.getLogger(name)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create file handler
    file_handler = logging.FileHandler(LOGS_DIR / 'app.log')
    file_handler.setFormatter(formatter)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Set log level
    logger.setLevel(logging.INFO)

    return logger
