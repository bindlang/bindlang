"""
Pluggable audit sink architecture for bindlang.

Provides Protocol interface and built-in file-based sinks for audit trail storage.
Enables custom storage backends (SQLite, Redis, S3) as opt-in extensions.
"""

from typing import Protocol, List, Optional, TextIO
from pathlib import Path
import json

from .models import BindingAttempt


class AuditSink(Protocol):
    """Protocol for pluggable audit trail storage.

    This defines the interface for custom audit storage backends.
    Core provides file-based implementations; users can implement
    custom sinks (SQLite, Redis, S3, etc.) without modifying core.

    Example:
        class CustomSink:
            def write(self, attempt: BindingAttempt) -> None:
                # Custom storage logic
                pass

            def flush(self) -> None:
                # Flush buffered data
                pass

            def close(self) -> None:
                # Cleanup resources
                pass
    """

    def write(self, attempt: BindingAttempt) -> None:
        """Write a single binding attempt to storage."""
        ...

    def flush(self) -> None:
        """Flush any buffered data to storage."""
        ...

    def close(self) -> None:
        """Close storage connection and cleanup resources."""
        ...


class JSONLFileSink:
    """Built-in sink for streaming JSONL (newline-delimited JSON) files.

    Each binding attempt is written as a single JSON object on one line.
    Ideal for streaming, large datasets, and line-based processing tools.

    Args:
        file_path: Path to output file (created if doesn't exist)
        buffer_size: Number of attempts to buffer before flushing (default: 10)
        append: If True, append to existing file; if False, overwrite (default: True)

    Example:
        sink = JSONLFileSink("audit.jsonl", buffer_size=10)
        engine = BindingEngine(audit_sink=sink)
    """

    def __init__(
        self,
        file_path: str,
        buffer_size: int = 10,
        append: bool = True
    ):
        self.file_path = Path(file_path)
        self.buffer_size = buffer_size
        self._buffer: List[BindingAttempt] = []
        self._file_handle: Optional[TextIO] = None

        # Create parent directories if needed
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Open file in append or write mode
        mode = 'a' if append else 'w'
        self._file_handle = open(self.file_path, mode, encoding='utf-8')

    def write(self, attempt: BindingAttempt) -> None:
        """Buffer attempt and flush when buffer is full."""
        self._buffer.append(attempt)

        if len(self._buffer) >= self.buffer_size:
            self.flush()

    def flush(self) -> None:
        """Write all buffered attempts as JSONL."""
        if not self._file_handle or not self._buffer:
            return

        # Write each attempt as a single JSON line
        for attempt in self._buffer:
            json_str = attempt.model_dump_json()
            self._file_handle.write(json_str + '\n')

        # Flush to disk
        self._file_handle.flush()

        # Clear buffer
        self._buffer.clear()

    def close(self) -> None:
        """Flush remaining buffer and close file handle."""
        if self._file_handle:
            self.flush()  # Flush remaining buffer
            self._file_handle.close()
            self._file_handle = None


class JSONFileSink:
    """Built-in sink for writing complete JSON arrays to file.

    Collects all binding attempts and writes them as a single JSON array.
    Ideal for smaller datasets and when you need a single JSON document.

    Args:
        file_path: Path to output file (created if doesn't exist)

    Example:
        sink = JSONFileSink("audit.json")
        engine = BindingEngine(audit_sink=sink)

    Note:
        All attempts are held in memory until close() is called.
        For large datasets, prefer JSONLFileSink for streaming.
    """

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self._attempts: List[BindingAttempt] = []

        # Create parent directories if needed
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, attempt: BindingAttempt) -> None:
        """Accumulate attempt in memory."""
        self._attempts.append(attempt)

    def flush(self) -> None:
        """No-op for JSON array sink (writes on close)."""
        pass

    def close(self) -> None:
        """Write all attempts as a single JSON array."""
        if not self._attempts:
            return

        # Convert attempts to JSON-serializable dicts
        attempts_data = [attempt.model_dump() for attempt in self._attempts]

        # Write as pretty-printed JSON array
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(attempts_data, f, indent=2, ensure_ascii=False)

        # Clear accumulated attempts
        self._attempts.clear()
