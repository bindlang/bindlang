"""
Export functionality for audit trails and ledgers.

Supports JSON and JSONL formats.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import BindingAttempt
from .state import StateTransition

# Version imported at module level to avoid circular import
def _get_version() -> str:
    try:
        from bindlang import __version__
        return __version__
    except ImportError:
        return "0.1.0"


class AuditExporter:
    """Handles audit trail export to JSON and JSONL."""

    @staticmethod
    def to_json(
        attempts: List[BindingAttempt],
        filepath: str,
        include_metadata: bool = True
    ) -> None:
        """Export audit trail to JSON format."""
        export_data: Dict[str, Any] = {}

        if include_metadata:
            export_data["metadata"] = AuditExporter.get_export_metadata(attempts)

        export_data["audit_trail"] = [
            a.model_dump(mode="json") for a in attempts
        ]

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def to_jsonl(attempts: List[BindingAttempt], filepath: str) -> None:
        """Export audit trail to JSONL format."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            for attempt in attempts:
                json_str = attempt.model_dump_json()
                f.write(json_str + '\n')

    @staticmethod
    def get_export_metadata(attempts: List[BindingAttempt]) -> Dict[str, Any]:
        """Generate metadata summary for export."""
        total = len(attempts)
        successes = sum(1 for a in attempts if a.success)
        failures = total - successes

        failure_types: Dict[str, int] = {}
        for attempt in attempts:
            if not attempt.success:
                for reason in attempt.failure_reasons:
                    ct = reason.condition_type
                    failure_types[ct] = failure_types.get(ct, 0) + 1

        return {
            "export_timestamp": datetime.now().isoformat(),
            "bindlang_version": _get_version(),
            "total_attempts": total,
            "success_count": successes,
            "failure_count": failures,
            "success_rate": (successes / total * 100) if total > 0 else 0.0,
            "failure_type_breakdown": failure_types
        }


class LedgerExporter:
    """Handles state transition ledger export to JSON and JSONL."""

    @staticmethod
    def to_json(
        transitions: List[StateTransition],
        filepath: str,
        include_metadata: bool = True
    ) -> None:
        """Export state transition ledger to JSON format."""
        export_data: Dict[str, Any] = {}

        if include_metadata:
            state_counts: Dict[str, int] = {}
            for t in transitions:
                key = f"{t.from_state.value} → {t.to_state.value}"
                state_counts[key] = state_counts.get(key, 0) + 1

            export_data["metadata"] = {
                "export_timestamp": datetime.now().isoformat(),
                "bindlang_version": _get_version(),
                "total_transitions": len(transitions),
                "transition_breakdown": state_counts
            }

        export_data["ledger"] = [
            t.model_dump(mode="json") for t in transitions
        ]

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def to_jsonl(transitions: List[StateTransition], filepath: str) -> None:
        """Export state transition ledger to JSONL format."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            for transition in transitions:
                json_str = transition.model_dump_json()
                f.write(json_str + '\n')


def export_attempts_filtered(
    attempts: List[BindingAttempt],
    filepath: str,
    fmt: str = "json",
    success: Optional[bool] = None
) -> int:
    """Export filtered subset of attempts, returns count exported."""
    if success is not None:
        filtered = [a for a in attempts if a.success == success]
    else:
        filtered = attempts

    if fmt == "json":
        AuditExporter.to_json(filtered, filepath)
    elif fmt == "jsonl":
        AuditExporter.to_jsonl(filtered, filepath)
    else:
        raise ValueError(f"Unsupported format: {fmt}")

    return len(filtered)
