"""
Audit trail management for BindingEngine.

Handles recording and querying of binding attempts, failures, and diagnostics.
"""

from typing import Dict, List, Optional, TYPE_CHECKING

from .models import BindingAttempt

if TYPE_CHECKING:
    from .engine import BindingEngine


class AuditManager:
    """Manages audit trail and failure analysis."""

    def __init__(self, engine: 'BindingEngine'):
        self.engine = engine
        self.trail: List[BindingAttempt] = []

    def record_attempt(self, attempt: BindingAttempt) -> None:
        """Record a binding attempt."""
        self.trail.append(attempt)

    def failed(self, symbol_id: str) -> List[BindingAttempt]:
        """Get all failed binding attempts for a symbol."""
        return [
            attempt for attempt in self.trail
            if attempt.symbol_id == symbol_id and not attempt.success
        ]

    def explain(self, symbol_id: str) -> str:
        """Get human-readable explanation of why symbol didn't activate."""
        # Get ALL attempts for this symbol
        all_attempts = self.attempts(symbol_id)

        if not all_attempts:
            return f"Symbol '{symbol_id}' was never attempted for binding"

        # Get most recent attempt
        latest = all_attempts[-1]

        # If most recent attempt was successful, report success
        if latest.success:
            return f"Symbol '{symbol_id}' successfully activated"

        # Most recent attempt failed - explain why
        if not latest.failure_reasons:
            return f"Symbol '{symbol_id}' failed to activate (no specific reason recorded)"

        # Build detailed explanation
        lines = [f"Symbol '{symbol_id}' failed to activate:"]
        for reason in latest.failure_reasons:
            lines.append(f"  - {reason.message}")

        return "\n".join(lines)

    def stats(self) -> Dict[str, int]:
        """Get aggregate statistics on failure types."""
        stats: Dict[str, int] = {}

        for attempt in self.trail:
            if not attempt.success:
                for reason in attempt.failure_reasons:
                    condition_type = reason.condition_type
                    stats[condition_type] = stats.get(condition_type, 0) + 1

        return stats

    def attempts(self, symbol_id: Optional[str] = None) -> List[BindingAttempt]:
        """Get all binding attempts (optionally filtered by symbol_id)."""
        if symbol_id is None:
            return list(self.trail)

        return [a for a in self.trail if a.symbol_id == symbol_id]
