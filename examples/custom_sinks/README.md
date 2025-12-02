# Custom Audit Sinks

Examples of custom `AuditSink` implementations for different storage backends.

## AuditSink Protocol

Implement three methods:

```python
class AuditSink(Protocol):
    def write(self, attempt: BindingAttempt) -> None:
        """Write a single binding attempt to storage."""
        ...

    def flush(self) -> None:
        """Flush any buffered data to storage."""
        ...

    def close(self) -> None:
        """Close storage connection and cleanup resources."""
        ...
```

## Examples

- **`inmemory_sink.py`** - Simple in-memory sink for testing
- **`sqlite_sink.py`** - Persistent SQLite database storage
- **`multiplex_sink.py`** - Fan-out to multiple sinks simultaneously

## Usage

```python
from bindlang import BindingEngine
from custom_sinks.sqlite_sink import SQLiteSink

sink = SQLiteSink("audit.db")
with BindingEngine(audit_sink=sink) as engine:
    # ... register and bind symbols ...
    pass
```
