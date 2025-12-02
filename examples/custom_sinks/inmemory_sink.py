"""
In-memory audit sink for testing.

Simple sink that stores all binding attempts in memory.
Useful for testing without file I/O overhead.
"""

from typing import List
from bindlang.core.models import BindingAttempt


class InMemorySink:
    """In-memory sink for testing (no persistence)."""

    def __init__(self):
        self.attempts: List[BindingAttempt] = []
        self.flush_count = 0

    def write(self, attempt: BindingAttempt) -> None:
        """Store attempt in memory."""
        self.attempts.append(attempt)

    def flush(self) -> None:
        """No-op (already in memory)."""
        self.flush_count += 1

    def close(self) -> None:
        """No resources to cleanup."""
        pass

    def get_failures(self) -> List[BindingAttempt]:
        """Helper: Get all failed attempts."""
        return [a for a in self.attempts if not a.success]

    def get_successes(self) -> List[BindingAttempt]:
        """Helper: Get all successful attempts."""
        return [a for a in self.attempts if a.success]


# Example usage
if __name__ == "__main__":
    from datetime import datetime
    from bindlang import BindingEngine, LatentSymbol, GateCondition, Context

    sink = InMemorySink()

    with BindingEngine(audit_sink=sink) as engine:
        symbol = LatentSymbol(
            id="test_symbol",
            symbol_type="EVENT:test",
            gate=GateCondition(who={"alice"}),
            payload={"message": "test"}
        )
        engine.register(symbol)

        # Success
        engine.bind(symbol, Context(who="alice", when=datetime.now(), where="test"))

        # Failure
        engine.bind(symbol, Context(who="bob", when=datetime.now(), where="test"))

    print(f"Total attempts: {len(sink.attempts)}")
    print(f"Successes: {len(sink.get_successes())}")
    print(f"Failures: {len(sink.get_failures())}")
    print(f"Flush count: {sink.flush_count}")
