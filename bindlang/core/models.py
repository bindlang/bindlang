"""
Core bindlang models.

Defines latent symbols, gate conditions, contexts, and audit trail structures.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Set

from pydantic import BaseModel, Field, field_validator
from pydantic import ConfigDict


class Evaluable(Protocol):
    """Protocol for anything that can evaluate against a context."""

    def evaluate(self, context: 'Context') -> bool:
        ...


class DateTimeTemporal(BaseModel):
    """Temporal condition based on datetime comparison."""

    model_config = ConfigDict(frozen=True)

    operator: str  # "after" or "before"
    reference: datetime  # Parsed datetime to compare against

    def evaluate(self, context: 'Context') -> bool:
        """Compare context.when against reference datetime."""
        if self.operator == "after":
            return context.when > self.reference
        elif self.operator == "before":
            return context.when < self.reference
        return False


class StateTemporal(BaseModel):
    """Temporal condition based on state lookup."""

    model_config = ConfigDict(frozen=True)

    state_key: str  # Key to look up in context.state

    def evaluate(self, context: 'Context') -> bool:
        """Check if state[key] is truthy."""
        return bool(context.state.get(self.state_key))


class TemporalExpression:
    """Factory for parsing temporal expressions."""

    @classmethod
    def parse(cls, expr: str) -> Evaluable:
        """Parse temporal expression, returns DateTimeTemporal or StateTemporal."""
        if ":" not in expr:
            raise ValueError(f"Invalid temporal expression: '{expr}' (missing ':')")

        operator, reference = expr.split(":", 1)

        if operator not in ("after", "before"):
            raise ValueError(f"Invalid operator: '{operator}' (must be 'after' or 'before')")

        # Check if reference looks like ISO datetime (starts with digit)
        if reference and reference[0].isdigit():
            try:
                ref_dt = datetime.fromisoformat(reference)
                return DateTimeTemporal(operator=operator, reference=ref_dt)
            except ValueError as e:
                raise ValueError(f"Invalid ISO datetime: '{reference}'") from e

        # Otherwise, it's a symbolic state reference
        return StateTemporal(state_key=reference)


class GateCondition(BaseModel):
    """Condition that must hold for symbol activation."""

    model_config = ConfigDict(frozen=True)

    who: Optional[Set[str]] = None
    when: Optional[str] = None  # e.g. "after:2024-01-01" or "before:deadline"
    where: Optional[Set[str]] = None
    state: Optional[Dict[str, Any]] = None

    def evaluate(self, context: 'Context') -> bool:
        """Evaluate all predicates against context."""
        # Check actor
        if self.who is not None and context.who not in self.who:
            return False

        # Check temporal predicate
        if self.when:
            expr = TemporalExpression.parse(self.when)
            if not expr.evaluate(context):
                return False

        # Check location
        if self.where is not None and context.where not in self.where:
            return False

        # Check state predicates
        if self.state:
            for key, expected in self.state.items():
                if context.state.get(key) != expected:
                    return False

        return True


class LatentSymbol(BaseModel):
    """Portable carrier of dormant meaning awaiting context."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique identifier for the symbol")
    symbol_type: str = Field(
        ...,
        description="Symbol type in the form CATEGORY:name",
        pattern=r"^[A-Z]+:[a-z_]+$|^[A-Z]+:[a-z]+$",
    )
    gate: GateCondition
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    consumption: str = Field(
        default="one_shot",
        description="Consumption mode: 'one_shot' (ticket burns after binding) or 'reusable' (stays latent)"
    )

    @field_validator('consumption')
    @classmethod
    def validate_consumption(cls, v: str) -> str:
        """Validate consumption mode is one of the allowed values."""
        if v not in ("one_shot", "reusable"):
            raise ValueError(f"consumption must be 'one_shot' or 'reusable', got '{v}'")
        return v

    def __str__(self) -> str:
        return f"⟦{self.symbol_type}⟧"


class BoundSymbol(BaseModel):
    """Symbol that has successfully bound against a context."""

    symbol_id: str
    symbol_type: str
    effect: Dict[str, Any]
    weight: float = 1.0
    bound_at: datetime = Field(default_factory=datetime.now)
    context_snapshot: Dict[str, Any]
    state_changes_applied: Optional[List[Dict[str, Any]]] = None  # Track actual state changes (old→new)


class Context(BaseModel):
    """Immutable runtime context for binding symbols.

    who: Optional[str] - Actor/witness perspective
        - Specific actor: "researcher_a", "alice", etc.
        - System/omniscient: None (no specific actor)
    """

    model_config = ConfigDict(frozen=True)

    who: Optional[str] = None
    when: datetime
    where: str
    state: Dict[str, Any] = Field(default_factory=dict)

    def with_state_update(self, key: str, value: Any) -> 'Context':
        """Return new Context with updated state key/value."""
        new_state = dict(self.state)
        new_state[key] = value
        return self.model_copy(update={"state": new_state})


class FailureReason(BaseModel):
    """Structured explanation of why gate condition failed."""

    model_config = ConfigDict(frozen=True)

    condition_type: str  # "who" | "when" | "where" | "state" | "dependency" | "expired"
    expected: Any  # What the gate required
    actual: Any  # What the context provided
    message: str  # Human-readable explanation


class BindingAttempt(BaseModel):
    """Record of a binding attempt (success or failure)."""

    model_config = ConfigDict(frozen=True)

    # Identity
    symbol_id: str
    attempt_timestamp: datetime = Field(default_factory=datetime.now)

    # Context at time of attempt
    context_snapshot: Dict[str, Any]

    # Result
    success: bool

    # If successful - reference to created BoundSymbol
    bound_symbol_id: Optional[str] = None

    # If failed - structured reasons
    failure_reasons: List[FailureReason] = Field(default_factory=list)

    # If successful with state mutations - track what changed
    state_changes_applied: Optional[List[Dict[str, Any]]] = None
