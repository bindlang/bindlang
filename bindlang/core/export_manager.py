"""
Export management for BindingEngine.

Handles exporting audit trails, failures, and ledgers to various formats.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import BindingEngine


class ExportManager:
    """Manages export of audit trails, failures, and ledgers to files."""

    def __init__(self, engine: 'BindingEngine'):
        self.engine = engine

    def trail(self, filepath: str, fmt: str = "json") -> None:
        """Export full audit trail to file (json or jsonl)."""
        from .export import AuditExporter

        if fmt == "json":
            AuditExporter.to_json(self.engine.audit.trail, filepath)
        elif fmt == "jsonl":
            AuditExporter.to_jsonl(self.engine.audit.trail, filepath)
        else:
            raise ValueError(f"Unsupported format: '{fmt}'. Use 'json' or 'jsonl'.")

    def failures(self, filepath: str, fmt: str = "json") -> int:
        """Export only failed attempts to file, returns count exported."""
        from .export import AuditExporter

        failures = [a for a in self.engine.audit.trail if not a.success]

        if fmt == "json":
            AuditExporter.to_json(failures, filepath)
        elif fmt == "jsonl":
            AuditExporter.to_jsonl(failures, filepath)
        else:
            raise ValueError(f"Unsupported format: '{fmt}'. Use 'json' or 'jsonl'.")

        return len(failures)

    def ledger(self, filepath: str, fmt: str = "json") -> None:
        """Export state transition ledger to file (json or jsonl)."""
        from .export import LedgerExporter

        if fmt == "json":
            LedgerExporter.to_json(self.engine.ledger, filepath)
        elif fmt == "jsonl":
            LedgerExporter.to_jsonl(self.engine.ledger, filepath)
        else:
            raise ValueError(f"Unsupported format: '{fmt}'. Use 'json' or 'jsonl'.")
