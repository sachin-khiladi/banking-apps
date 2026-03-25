"""Azure Application Insights logging via OpenTelemetry.

Exports logs to Azure Monitor when APPLICATIONINSIGHTS_CONNECTION_STRING is set.
Falls back to a stdout StreamHandler for local development — no credentials needed.

Environment variables:
  APPLICATIONINSIGHTS_CONNECTION_STRING  — Azure Monitor connection string (optional locally).
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure application logging.

    When APPLICATIONINSIGHTS_CONNECTION_STRING is present, attempts to wire up
    azure-monitor-opentelemetry-exporter.  Falls back to a plain StreamHandler
    when the env var is absent (local dev) or the exporter package is missing.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )

    connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
    if not connection_string:
        logger.info(
            "APPLICATIONINSIGHTS_CONNECTION_STRING not set — using stdout logging only."
        )
        return

    try:
        from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter  # type: ignore
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler  # type: ignore
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor  # type: ignore

        exporter = AzureMonitorLogExporter(connection_string=connection_string)
        provider = LoggerProvider()
        provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
        handler = LoggingHandler(logger_provider=provider)
        logging.getLogger().addHandler(handler)
        logger.info("Azure Application Insights logging configured.")
    except ImportError:
        logger.warning(
            "azure-monitor-opentelemetry-exporter not installed — "
            "falling back to stdout logging."
        )


def log_event(event_name: str, properties: dict | None = None) -> None:
    """Log a named application event."""
    logger.info(event_name, extra=properties or {})


def log_exception(exception: Exception) -> None:
    """Log an exception with traceback."""
    logger.exception("An exception occurred", exc_info=exception)
