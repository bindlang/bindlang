"""
State machine for symbol lifecycle tracking.

Defines states and validates transitions:
- One-shot symbols: CREATED → DORMANT → ACTIVATED → ARCHIVED
- Reusable symbols: ACTIVATED can return to DORMANT for re-evaluation
- Expiration: DORMANT → EXPIRED (gate conditions never satisfied)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class SymbolState(Enum):
    """Enumerated lifecycle states for latent symbols."""

    CREATED = "created"
    DORMANT = "dormant"
    ACTIVATED = "activated"
    ARCHIVED = "archived"
    EXPIRED = "expired"


class SymbolStateMachine:
    """Validate legal transitions between symbol states."""

    TRANSITIONS = {
        SymbolState.CREATED: {SymbolState.DORMANT},
        SymbolState.DORMANT: {SymbolState.ACTIVATED, SymbolState.EXPIRED},
        SymbolState.ACTIVATED: {SymbolState.ARCHIVED, SymbolState.DORMANT},  # DORMANT for reusable consumption
    }

    @classmethod
    def validate(cls, from_state: SymbolState, to_state: SymbolState) -> bool:
        """Return True if `to_state` is reachable from `from_state`."""
        return to_state in cls.TRANSITIONS.get(from_state, set())


class StateTransition(BaseModel):
    """Record of a single state transition for a symbol."""

    symbol_id: str
    from_state: SymbolState
    to_state: SymbolState
    timestamp: datetime = Field(default_factory=datetime.now)
    reason: str

    @model_validator(mode="after")
    def validate_transition(self) -> 'StateTransition':
        """Ensure that the transition is permitted by the state machine."""
        if not SymbolStateMachine.validate(self.from_state, self.to_state):
            raise ValueError(
                f"Invalid transition: {self.from_state.value} -> {self.to_state.value}"
            )
        return self
