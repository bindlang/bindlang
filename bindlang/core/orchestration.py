"""
Multi-Actor Orchestration for bindlang.

Provides ActorSequenceRunner for executing binding across multiple actor perspectives,
carrying state mutations between contexts.

Design Principle:
- Context = ONE actor's perspective (witness/speaker)
- who = the witness/speaker performing the evaluation
- state = world state (who is present, what has happened)

Multi-actor coordination via:
  (a) state-tracking of actor presence/actions
  (b) explicit sequencing of different who-contexts
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .engine import BindingEngine
from .models import BoundSymbol, Context


class ActorSequenceRunner:
    """
    Multi-actor execution orchestrator.

    Executes binding from multiple actor perspectives in sequence,
    carrying state mutations between contexts.

    This is the canonical pattern for multi-actor scenarios in bindlang.

    Design Principles:
    -----------------
    1. Context represents ONE actor's perspective (witness)
       - who: Optional[str] - The actor/witness performing the evaluation
       - who=None - System/omniscient perspective (no specific actor)

    2. State carries factual information
       - Which actors are present: {"researcher_a_present": true}
       - What has happened: {"experiment_complete": true}
       - World state: {"door_locked": false}

    3. who-gate vs state-gate distinction:
       - who-gate: ownership/agency of the action
       - state-gate: factual preconditions that must hold

    Example Usage:
    -------------
    >>> engine = BindingEngine()
    >>> # Register symbols...
    >>>
    >>> runner = ActorSequenceRunner(engine)
    >>>
    >>> # Define actor sequence
    >>> actor_contexts = [
    ...     {"who": None, "where": "lab_entrance"},           # System: lab opens
    ...     {"who": "researcher_a", "where": "lab_entrance"}, # A arrives
    ...     {"who": "researcher_b", "where": "lab_entrance"}, # B arrives
    ...     {"who": None, "where": "main_lab"},               # System: collaboration starts
    ... ]
    >>>
    >>> bound, final_state = runner.run_actor_sequence(
    ...     actor_contexts,
    ...     initial_state={"lab_open": False}
    ... )
    >>>
    >>> # Result: all symbols from all perspectives, with carried state
    """

    def __init__(self, engine: BindingEngine):
        """
        Initialize with a BindingEngine instance.

        Args:
            engine: BindingEngine with registered symbols
        """
        self.engine = engine

    def run_actor_sequence(
        self,
        actor_contexts: List[Dict[str, Any]],
        initial_state: Optional[Dict[str, Any]] = None,
        initial_when: Optional[datetime] = None,
    ) -> Tuple[List[BoundSymbol], Dict[str, Any]]:
        """
        Execute binding across multiple actor perspectives.

        State mutations from each perspective are carried forward to the next,
        enabling reactive multi-actor coordination.

        Args:
            actor_contexts: List of context templates, each with:
                - who: Optional[str] - Actor identifier (None for system perspective)
                - where: str - Location (optional, defaults to "")
                - when: datetime (optional, uses initial_when or now())
            initial_state: Initial world state (defaults to {})
            initial_when: Initial timestamp (defaults to datetime.now())

        Returns:
            Tuple of:
            - all_bound: List of all BoundSymbols from all perspectives (in order)
            - final_state: Final state after all actor perspectives

        Example:
            >>> actor_contexts = [
            ...     {"who": None, "where": "lobby"},
            ...     {"who": "alice", "where": "lobby"},
            ...     {"who": "bob", "where": "lobby"},
            ... ]
            >>> bound, state = runner.run_actor_sequence(
            ...     actor_contexts,
            ...     initial_state={"door_open": False}
            ... )
        """
        if initial_state is None:
            initial_state = {}

        if initial_when is None:
            initial_when = datetime.now()

        all_bound: List[BoundSymbol] = []
        current_state = initial_state.copy()

        for ctx_template in actor_contexts:
            # Extract context parameters
            who = ctx_template.get("who")
            where = ctx_template.get("where", "")
            when = ctx_template.get("when", initial_when)

            # Create full context with current state
            context = Context(
                who=who,
                where=where,
                when=when,
                state=current_state,
            )

            # Execute binding for this perspective
            bound_symbols, final_ctx = self.engine.bind_all_registered(
                context, apply_state_mutations=True
            )

            # Collect results
            all_bound.extend(bound_symbols)

            # Carry state forward to next perspective
            current_state = dict(final_ctx.state)

        return all_bound, current_state

    def run_with_timeline(
        self,
        actor_timeline: List[Tuple[datetime, Optional[str], str]],
        initial_state: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[BoundSymbol], Dict[str, Any]]:
        """
        Execute binding with explicit timeline of (when, who, where) tuples.

        Useful for scenarios with temporal progression.

        Args:
            actor_timeline: List of (when, who, where) tuples
                Example:
                [
                    (datetime(2025, 11, 19, 9, 0), None, "lab_entrance"),
                    (datetime(2025, 11, 19, 9, 5), "researcher_a", "lab_entrance"),
                    (datetime(2025, 11, 19, 9, 10), "researcher_b", "lab_entrance"),
                ]
            initial_state: Initial world state

        Returns:
            Same as run_actor_sequence()
        """
        actor_contexts = [
            {"who": who, "where": where, "when": when} for when, who, where in actor_timeline
        ]

        return self.run_actor_sequence(actor_contexts, initial_state)
