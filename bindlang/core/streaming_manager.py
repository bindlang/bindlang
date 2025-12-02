"""
Streaming mode management for BindingEngine.

Handles auto-writing audit trail to disk in real-time using pluggable sinks.
"""

from typing import Optional, TYPE_CHECKING

from .models import BindingAttempt
from .sinks import AuditSink

if TYPE_CHECKING:
    from .engine import BindingEngine


class StreamingManager:
    """Manages streaming mode for auto-writing audit trail via pluggable sinks."""

    def __init__(
        self,
        engine: 'BindingEngine',
        audit_sink: Optional[AuditSink] = None
    ):
        """Initialize streaming manager.

        Args:
            engine: Parent BindingEngine instance
            audit_sink: Optional sink for audit trail storage

        Example:
            from bindlang.core.sinks import JSONLFileSink
            sink = JSONLFileSink("audit.jsonl", buffer_size=10)
            manager = StreamingManager(engine, audit_sink=sink)
        """
        self.engine = engine
        self._sink: Optional[AuditSink] = audit_sink

    def record_attempt(self, attempt: BindingAttempt) -> None:
        """Record attempt in audit manager and write to sink."""
        # Always record in audit manager first
        self.engine.audit.record_attempt(attempt)

        # Write to sink if configured
        if self._sink:
            self._sink.write(attempt)

    def flush(self) -> None:
        """Flush buffered attempts to storage via sink."""
        if self._sink:
            self._sink.flush()

    def close(self) -> None:
        """Close sink and cleanup resources."""
        if self._sink:
            self._sink.close()
            self._sink = None
