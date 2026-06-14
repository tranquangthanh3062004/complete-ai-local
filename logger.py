import logging
import os
from logging.handlers import RotatingFileHandler
from config import settings

# Create logs directory if it doesn't exist
os.makedirs(settings.log_dir, exist_ok=True)

# Define log file path
log_file = os.path.join(settings.log_dir, "gtcc_bot.log")

# Setup logger
logger = logging.getLogger("gtcc_bot")
logger.setLevel(logging.INFO if not settings.debug else logging.DEBUG)

# File handler with rotation (max 5MB per file, keep 3 backups)
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
file_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(file_formatter)

# Console handler
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S"
)
console_handler.setFormatter(console_formatter)

# Add handlers
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def get_logger(name: str):
    return logger.getChild(name)
