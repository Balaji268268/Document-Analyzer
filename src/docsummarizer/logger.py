"""
Logging and Diagnostics Module
Provides logging functionality and system diagnostics for DocSummarizer.
"""

import logging
import os
import platform
import sys
from datetime import datetime
from pathlib import Path


def get_log_directory() -> Path:
    """Get the directory where logs are stored."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    log_dir = base / "DocSummarizer" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logger(name: str = "DocSummarizer") -> logging.Logger:
    """Set up and return a logger that writes to file and optionally console."""
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Create log file with date
    log_dir = get_log_directory()
    log_file = log_dir / f"docsummarizer_{datetime.now().strftime('%Y%m%d')}.log"

    # File handler - detailed logging
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


# Global logger instance
# `_logger_lock` protects the lazy init so two threads calling get_logger()
# before _logger is set don't both call setup_logger() and end up adding
# duplicate file handlers to the same logger.
_logger: logging.Logger | None = None
_logger_lock = threading.Lock()


def get_logger() -> logging.Logger:
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        with _logger_lock:
            if _logger is None:
                _logger = setup_logger()
    return _logger


def log_info(message: str):
    """Log an info message."""
    get_logger().info(message)


def log_debug(message: str):
    """Log a debug message."""
    get_logger().debug(message)


def log_warning(message: str):
    """Log a warning message."""
    get_logger().warning(message)


def log_error(message: str):
    """Log an error message."""
    get_logger().error(message)


def get_system_info() -> dict:
    """Gather system diagnostic information."""
    info = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "platform_release": platform.release(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version,
        "cpu_count": os.cpu_count(),
    }

    # Try to get memory info
    try:
        import psutil

        mem = psutil.virtual_memory()
        info["total_memory_gb"] = round(mem.total / (1024**3), 2)
        info["available_memory_gb"] = round(mem.available / (1024**3), 2)
        info["memory_percent_used"] = mem.percent
    except ImportError:
        info["memory_info"] = "psutil not available"

    return info


def log_system_info():
    """Log system diagnostic information."""
    logger = get_logger()
    info = get_system_info()

    logger.info("=" * 60)
    logger.info("SYSTEM DIAGNOSTICS")
    logger.info("=" * 60)
    logger.info(f"Platform: {info['platform']} {info['platform_release']}")
    logger.info(f"Architecture: {info['architecture']}")
    logger.info(f"CPU Cores: {info['cpu_count']}")
    logger.info(f"Python: {info['python_version'].split()[0]}")

    if "total_memory_gb" in info:
        logger.info(f"Total Memory: {info['total_memory_gb']} GB")
        logger.info(
            f"Available Memory: {info['available_memory_gb']} GB ({100 - info['memory_percent_used']:.1f}% free)"
        )

    logger.info("=" * 60)


def log_startup():
    """Log application startup."""
    logger = get_logger()
    logger.info("")
    logger.info("*" * 60)
    logger.info("DocSummarizer Starting")
    logger.info(f"Startup time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("*" * 60)
    log_system_info()


def get_memory_usage_mb() -> float:
    """Get current process memory usage in MB."""
    try:
        import psutil

        process = psutil.Process(os.getpid())
        return round(process.memory_info().rss / (1024**2), 2)
    except ImportError:
        return 0.0


def get_cpu_percent() -> float:
    """Get current process CPU usage percent."""
    try:
        import psutil

        process = psutil.Process(os.getpid())
        return process.cpu_percent(interval=0.1)
    except ImportError:
        return 0.0


class Timer:
    """Simple timer for measuring operation duration."""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        log_info(f"Starting: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()

        if exc_type is not None:
            log_error(f"Failed: {self.operation_name} after {duration:.2f}s - {exc_val}")
        else:
            log_info(f"Completed: {self.operation_name} in {duration:.2f}s")

        return False  # Don't suppress exceptions
