"""
Logger - Vercel/Cloud compatible.
Trên Vercel filesystem là read-only → chỉ dùng StreamHandler (stdout).
Khi chạy local, nếu có thể ghi file thì thêm RotatingFileHandler.
"""
import logging
import os
import sys
from config import settings

def _setup_logger() -> logging.Logger:
    log = logging.getLogger("gtcc_bot")
    log.setLevel(logging.INFO if not settings.debug else logging.DEBUG)

    if log.handlers:
        return log

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )

    # Always add stdout handler (works on Vercel)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    log.addHandler(stream_handler)

    # Try file handler only when filesystem is writable (local dev)
    try:
        log_dir = settings.log_dir
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "gtcc_bot.log")
        # Quick write-test
        with open(log_file, "a") as _f:
            pass
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(fmt)
        log.addHandler(file_handler)
    except OSError:
        # Vercel / read-only FS → skip file logging silently
        pass

    return log


_root_logger = _setup_logger()


def get_logger(name: str) -> logging.Logger:
    return _root_logger.getChild(name)
