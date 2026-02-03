import logging
import sys
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional


# -----------------------------------------------------------------------------
# Logger configuration
# -----------------------------------------------------------------------------

def setup_logger(
    name: str = "hybrid-llm-agent",
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure a structured logger for the application.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger  # Prevent duplicate handlers

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = setup_logger()


# -----------------------------------------------------------------------------
# Correlation / Trace utilities
# -----------------------------------------------------------------------------

def generate_trace_id() -> str:
    """
    Generates a unique trace ID for request-level observability.
    """
    return str(uuid.uuid4())


# -----------------------------------------------------------------------------
# Structured logging helpers
# -----------------------------------------------------------------------------

def log_event(
    event: str,
    trace_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    level: int = logging.INFO,
):
    """
    Emit a structured log event.
    """
    payload = {
        "event": event,
        "trace_id": trace_id,
        "metadata": metadata or {},
    }
    logger.log(level, payload)


def log_error(
    event: str,
    error: Exception,
    trace_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Emit a structured error log.
    """
    payload = {
        "event": event,
        "trace_id": trace_id,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "metadata": metadata or {},
    }
    logger.error(payload)


# -----------------------------------------------------------------------------
# Timing / tracing context managers
# -----------------------------------------------------------------------------

@contextmanager
def trace_span(
    name: str,
    trace_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Context manager to trace execution time of a block.
    """
    start_time = time.perf_counter()
    log_event(
        event=f"{name}.start",
        trace_id=trace_id,
        metadata=metadata,
    )

    try:
        yield
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        log_event(
            event=f"{name}.end",
            trace_id=trace_id,
            metadata={
                **(metadata or {}),
                "duration_ms": duration_ms,
            },
        )
    except Exception as e:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        log_error(
            event=f"{name}.error",
            error=e,
            trace_id=trace_id,
            metadata={
                **(metadata or {}),
                "duration_ms": duration_ms,
            },
        )
        raise


# -----------------------------------------------------------------------------
# Specialized helpers for common operations
# -----------------------------------------------------------------------------

@contextmanager
def trace_tool(
    tool_name: str,
    trace_id: Optional[str] = None,
    input_metadata: Optional[Dict[str, Any]] = None,
):
    """
    Trace a tool invocation (vector search, graph query, OCR, web search).
    """
    with trace_span(
        name=f"tool.{tool_name}",
        trace_id=trace_id,
        metadata=input_metadata,
    ):
        yield


@contextmanager
def trace_ingestion_stage(
    stage_name: str,
    document_id: str,
    trace_id: Optional[str] = None,
):
    """
    Trace a specific ingestion pipeline stage.
    """
    with trace_span(
        name=f"ingestion.{stage_name}",
        trace_id=trace_id,
        metadata={"document_id": document_id},
    ):
        yield


@contextmanager
def trace_query_stage(
    stage_name: str,
    query: str,
    trace_id: Optional[str] = None,
):
    """
    Trace a query pipeline stage.
    """
    with trace_span(
        name=f"query.{stage_name}",
        trace_id=trace_id,
        metadata={"query": query},
    ):
        yield
