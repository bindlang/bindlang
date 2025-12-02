"""
Multiplex sink for writing to multiple sinks simultaneously.

Enables fan-out pattern: write to file AND database AND in-memory.
"""

from typing import List
from bindlang.core.models import BindingAttempt
from bindlang.core.sinks import AuditSink


class MultiplexSink:
    """Fan-out sink that writes to multiple underlying sinks."""

    def __init__(self, *sinks: AuditSink):
        """
        Initialize multiplex sink.

        Args:
            *sinks: Variable number of sinks to multiplex to

        Example:
            sink = MultiplexSink(
                JSONLFileSink("audit.jsonl"),
                SQLiteSink("audit.db"),
                InMemorySink()
            )
        """
        self.sinks: List[AuditSink] = list(sinks)

    def write(self, attempt: BindingAttempt) -> None:
        """Write to all sinks."""
        for sink in self.sinks:
            sink.write(attempt)

    def flush(self) -> None:
        """Flush all sinks."""
        for sink in self.sinks:
            sink.flush()

    def close(self) -> None:
        """Close all sinks."""
        for sink in self.sinks:
            sink.close()


# Example usage
if __name__ == "__main__":
    from datetime import datetime
    from bindlang import BindingEngine, LatentSymbol, GateCondition, Context
    from bindlang.core.sinks import JSONLFileSink
    from inmemory_sink import InMemorySink
    from sqlite_sink import SQLiteSink

    # Write to JSONL file, SQLite database, and in-memory simultaneously
    file_sink = JSONLFileSink("audit.jsonl", buffer_size=1)
    db_sink = SQLiteSink("audit.db")
    mem_sink = InMemorySink()

    multiplex = MultiplexSink(file_sink, db_sink, mem_sink)

    with BindingEngine(audit_sink=multiplex) as engine:
        symbol = LatentSymbol(
            id="multi_test",
            symbol_type="EVENT:test",
            gate=GateCondition(who={"alice"}),
            payload={"test": "multiplex"}
        )
        engine.register(symbol)

        engine.bind(symbol, Context(who="alice", when=datetime.now(), where="test"))
        engine.bind(symbol, Context(who="bob", when=datetime.now(), where="test"))

    # Verify all sinks received data
    print(f"In-memory attempts: {len(mem_sink.attempts)}")
    print(f"SQLite attempts: {len(db_sink.query_by_symbol('multi_test'))}")
    print("JSONL file created: audit.jsonl")
