import logging
import os

from datetime import datetime
from contextvars import ContextVar

# ==========================================================
# CONTEXT VARIABLES
# ==========================================================

correlation_id_var: ContextVar[str] = ContextVar(
    "correlation_id",
    default=""
)

trace_id_var: ContextVar[str] = ContextVar(
    "trace_id",
    default=""
)

span_id_var: ContextVar[str] = ContextVar(
    "span_id",
    default=""
)

user_id_var: ContextVar[str] = ContextVar(
    "user_id",
    default=""
)

request_id_var: ContextVar[str] = ContextVar(
    "request_id",
    default=""
)

# ==========================================================
# JSON LOGGER SUPPORT
# ==========================================================

try:
    from pythonjsonlogger import jsonlogger

    HAS_JSON_LOGGER = True

except ImportError:
    HAS_JSON_LOGGER = False

    print(
        "⚠️ python-json-logger not installed. Using standard logging."
    )


# ==========================================================
# CONTEXT FILTER
# ==========================================================

class ContextFilter(logging.Filter):

    def filter(self, record):

        record.correlation_id = correlation_id_var.get()
        record.trace_id = trace_id_var.get()
        record.span_id = span_id_var.get()
        record.user_id = user_id_var.get()
        record.request_id = request_id_var.get()

        return True


# ==========================================================
# CONFIGURE LOGGING
# ==========================================================

def configure_logging(
    log_level: str = "INFO",
    log_format: str = "json"
):

    level = getattr(
        logging,
        log_level.upper(),
        logging.INFO
    )

    os.makedirs("logs", exist_ok=True)

    root_logger = logging.getLogger()

    root_logger.setLevel(level)

    # Remove old handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # ======================================================
    # CONSOLE HANDLER
    # ======================================================

    console_handler = logging.StreamHandler()

    console_handler.setLevel(level)

    console_handler.addFilter(ContextFilter())

    # ======================================================
    # FILE HANDLER
    # ======================================================

    log_filename = (
        f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"
    )

    file_handler = logging.FileHandler(log_filename)

    file_handler.setLevel(level)

    file_handler.addFilter(ContextFilter())

    # ======================================================
    # FORMATTERS
    # ======================================================

    if HAS_JSON_LOGGER and log_format.lower() == "json":

        formatter = jsonlogger.JsonFormatter(
            fmt="""
                %(asctime)s
                %(levelname)s
                %(name)s
                %(message)s
                %(correlation_id)s
                %(trace_id)s
                %(span_id)s
                %(user_id)s
                %(request_id)s
            """
        )

    else:

        formatter = logging.Formatter(
            fmt=(
                "%(asctime)s | "
                "%(levelname)s | "
                "%(name)s | "
                "%(message)s | "
                "correlation_id=%(correlation_id)s"
            )
        )

    console_handler.setFormatter(formatter)

    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)

    root_logger.addHandler(file_handler)

    # ======================================================
    # REDUCE NOISY LOGS
    # ======================================================

    logging.getLogger("uvicorn").setLevel(logging.INFO)

    logging.getLogger("urllib3").setLevel(
        logging.WARNING
    )

    logging.getLogger("pymongo").setLevel(
        logging.WARNING
    )

    logging.getLogger("redis").setLevel(
        logging.WARNING
    )

    logging.getLogger("opentelemetry").setLevel(
        logging.WARNING
    )

    return root_logger


# ==========================================================
# GET LOGGER
# ==========================================================

def get_logger(name: str):

    return logging.getLogger(name)