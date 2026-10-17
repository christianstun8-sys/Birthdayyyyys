import logging
import sys

# Configure logging to output to console immediately
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
    force=True
)

def log(message, level='INFO'):
    levels = {
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "DEBUG": logging.DEBUG
    }
    logging.log(msg=f"{message}", level=levels.get(level, logging.INFO))
