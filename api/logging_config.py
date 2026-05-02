"""
Centralized logging configuration for ClawFlow API.
"""
import logging
import logging.handlers
import os


LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging with both console and rotating file output.

    - Console: human-readable format for development
    - File: rotated daily, kept for 7 days
    - Loggers:
        - "" (root) — all loggers inherit from this
        - "api" — all ClawFlow modules
        - "uvicorn" — HTTP server logs
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    console_level = getattr(logging, log_level.upper(), logging.INFO)

    CONSOLE_FMT = "%(asctime)s %(levelname)-8s %(name)-20s %(message)s"
    FILE_FMT = "%(asctime)s %(levelname)-8s %(name)-20s %(message)s"
    DATE_FMT = "%Y-%m-%d %H:%M:%S"

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Remove existing handlers
    for h in root.handlers[:]:
        root.removeHandler(h)

    # ── Console Handler ──────────────────────────────────────────────────────
    console = logging.StreamHandler()
    console.setLevel(console_level)
    console.setFormatter(logging.Formatter(CONSOLE_FMT, datefmt=DATE_FMT))
    root.addHandler(console)

    # ── File Handler (rotating daily, 7-day retention) ─────────────────────────
    file_handler = logging.handlers.TimedRotatingFileHandler(
        os.path.join(LOG_DIR, "clawflow.log"),
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(FILE_FMT, datefmt=DATE_FMT))
    root.addHandler(file_handler)

    # ── Error-only file ──────────────────────────────────────────────────────
    error_handler = logging.handlers.TimedRotatingFileHandler(
        os.path.join(LOG_DIR, "clawflow_error.log"),
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(FILE_FMT, datefmt=DATE_FMT))
    root.addHandler(error_handler)

    # Suppress noisy third-party loggers
    for noisy in ["uvicorn.access", "uvicorn.asgi", "httpx", "httpcore"]:
        l = logging.getLogger(noisy)
        l.setLevel(logging.WARNING)
