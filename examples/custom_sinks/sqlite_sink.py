"""
SQLite audit sink for persistent queryable storage.

Enables SQL queries over binding attempts for analysis and debugging.
"""

import sqlite3
import json
from pathlib import Path
from bindlang.core.models import BindingAttempt


class SQLiteSink:
    """SQLite database sink for persistent audit storage."""

    def __init__(self, db_path: str, table: str = "binding_attempts"):
        """
        Initialize SQLite sink.

        Args:
            db_path: Path to SQLite database file
            table: Table name for storing attempts
        """
        self.db_path = Path(db_path)
        self.table = table
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        """Create table if it doesn't exist."""
        self.conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol_id TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                context_snapshot TEXT,
                failure_reasons TEXT,
                bound_symbol_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                data TEXT
            )
        """)
        self.conn.commit()

    def write(self, attempt: BindingAttempt) -> None:
        """Write attempt to database."""
        data = attempt.model_dump_json()
        failure_reasons_json = json.dumps(
            [r.model_dump() for r in attempt.failure_reasons]
        ) if attempt.failure_reasons else None

        self.conn.execute(
            f"""
            INSERT INTO {self.table}
            (symbol_id, success, context_snapshot, failure_reasons, bound_symbol_id, data)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                attempt.symbol_id,
                attempt.success,
                json.dumps(attempt.context_snapshot),
                failure_reasons_json,
                attempt.bound_symbol_id,
                data
            )
        )

    def flush(self) -> None:
        """Commit pending transactions."""
        self.conn.commit()

    def close(self) -> None:
        """Commit and close database connection."""
        self.conn.commit()
        self.conn.close()

    # Helper query methods
    def query_failures(self, symbol_id: str = None):
        """Query failed attempts, optionally filtered by symbol."""
        query = f"SELECT * FROM {self.table} WHERE success = 0"
        params = ()

        if symbol_id:
            query += " AND symbol_id = ?"
            params = (symbol_id,)

        return self.conn.execute(query, params).fetchall()

    def query_by_symbol(self, symbol_id: str):
        """Query all attempts for a specific symbol."""
        return self.conn.execute(
            f"SELECT * FROM {self.table} WHERE symbol_id = ?",
            (symbol_id,)
        ).fetchall()


# Example usage
if __name__ == "__main__":
    from datetime import datetime
    from bindlang import BindingEngine, LatentSymbol, GateCondition, Context

    sink = SQLiteSink("audit.db")

    with BindingEngine(audit_sink=sink) as engine:
        symbol = LatentSymbol(
            id="admin_action",
            symbol_type="EVENT:action",
            gate=GateCondition(who={"admin"}),
            payload={"action": "deploy"}
        )
        engine.register(symbol)

        # Multiple binding attempts
        for user in ["admin", "user1", "user2", "admin"]:
            engine.bind(symbol, Context(who=user, when=datetime.now(), where="server"))

    # Query results
    print(f"All attempts: {len(sink.query_by_symbol('admin_action'))}")
    print(f"Failures: {len(sink.query_failures())}")

    sink.close()
