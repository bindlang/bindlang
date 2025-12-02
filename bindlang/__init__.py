"""
bindlang - Deferred semantic binding primitives.

Public API for creating latent symbols, gates, and binding against context.
"""

__version__ = "0.1.0"

from .core.engine import BindingEngine, CircularDependencyError
from .core.models import (
    TemporalExpression,
    DateTimeTemporal,
    StateTemporal,
    GateCondition,
    LatentSymbol,
    BoundSymbol,
    Context,
    FailureReason,
    BindingAttempt,
)
from .core.state import SymbolState, SymbolStateMachine, StateTransition
from .core.orchestration import ActorSequenceRunner

__all__ = [
    "__version__",
    "BindingEngine",
    "CircularDependencyError",
    "TemporalExpression",
    "DateTimeTemporal",
    "StateTemporal",
    "GateCondition",
    "LatentSymbol",
    "BoundSymbol",
    "Context",
    "FailureReason",
    "BindingAttempt",
    "SymbolState",
    "SymbolStateMachine",
    "StateTransition",
    "ActorSequenceRunner",
]
