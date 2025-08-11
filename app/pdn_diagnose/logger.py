import logging


def setup_logger(name='pdn_diagnose'):
    """Setup logger for pdn_diagnose module"""
    logger = logging.getLogger(name)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create console handler only
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    # Set log level
    logger.setLevel(logging.INFO)

    return logger
