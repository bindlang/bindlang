"""
Binding engine for bindlang.

Orchestrates symbol registration, binding evaluation, and state tracking.
Supports dependency resolution, audit trails, and streaming mode with pluggable sinks.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Callable, Tuple, Set, TYPE_CHECKING

from .models import (
    Context,
    LatentSymbol,
    BoundSymbol,
    BindingAttempt,
    FailureReason,
)
from .state import SymbolState, StateTransition
from .checkers import (
    WhoChecker,
    WhenChecker,
    WhereChecker,
    StateChecker,
    DependencyChecker,
    ExpirationChecker,
)
from .template_manager import TemplateManager
from .audit_manager import AuditManager
from .export_manager import ExportManager
from .streaming_manager import StreamingManager

if TYPE_CHECKING:
    from .sinks import AuditSink


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected in symbol registry."""
    pass


class BindingEngine:
    """Engine to manage latent symbols and bind them against contexts.

    Supports optional streaming mode for auto-writing audit trail via pluggable sinks.
    """

    def __init__(
        self,
        audit_sink: Optional['AuditSink'] = None,
        on_symbol_activated: Optional[Callable[[LatentSymbol, Context, BoundSymbol], None]] = None
    ) -> None:
        """Initialize the binding engine.

        Args:
            audit_sink: Optional pluggable sink for audit trail storage
            on_symbol_activated: Optional callback when a symbol activates

        Example:
            from bindlang.core.sinks import JSONLFileSink, JSONFileSink

            # Streaming JSONL (recommended for large datasets)
            sink = JSONLFileSink("audit.jsonl", buffer_size=10)
            engine = BindingEngine(audit_sink=sink)

            # Complete JSON array (good for smaller datasets)
            sink = JSONFileSink("audit.json")
            engine = BindingEngine(audit_sink=sink)

            # No audit sink (audit still tracked in memory)
            engine = BindingEngine()
        """
        # Core state
        self.ledger: List[StateTransition] = []
        self.symbol_registry: Dict[str, LatentSymbol] = {}
        self.activated_symbols: set[str] = set()

        # Dependency graph for circular detection (adjacency list)
        self.dependency_graph: Dict[str, List[str]] = {}

        # Event hook for activation callbacks
        self.on_symbol_activated = on_symbol_activated

        # Composition-based managers
        self.templates = TemplateManager(self)
        self.audit = AuditManager(self)
        self.export = ExportManager(self)
        self.streaming = StreamingManager(self, audit_sink=audit_sink)

    def register(self, symbol: LatentSymbol) -> None:
        """Register latent symbol (CREATED → DORMANT transition)."""
        self.symbol_registry[symbol.id] = symbol

        # Update dependency graph and check for cycles
        self.dependency_graph[symbol.id] = list(symbol.depends_on)
        self._validate_acyclic()

        # Record state transition: CREATED → DORMANT
        self._log(symbol.id, SymbolState.CREATED, SymbolState.DORMANT, "Registered")

    def bind(self, symbol: LatentSymbol, context: Context) -> Optional[BoundSymbol]:
        """Attempt to bind symbol against context, returns BoundSymbol or None."""
        # Run gate checks (ordered: cheap checks first, temporal last)
        checkers = [
            DependencyChecker(self.activated_symbols),
            ExpirationChecker(),
            WhoChecker(),
            WhereChecker(),
            StateChecker(),
            WhenChecker(),  # Temporal checks can be expensive
        ]

        failure_reasons: List[FailureReason] = []
        for checker in checkers:
            reason = checker.check(symbol, context)
            if reason:
                failure_reasons.append(reason)

        # Handle failure case
        if failure_reasons:
            attempt = BindingAttempt(
                symbol_id=symbol.id,
                context_snapshot=context.model_dump(),
                success=False,
                failure_reasons=failure_reasons,
            )
            self.streaming.record_attempt(attempt)

            # Update state if expired
            if any(r.condition_type == "expired" for r in failure_reasons):
                self._log(symbol.id, SymbolState.DORMANT, SymbolState.EXPIRED, "Deadline passed")

            return None

        # All checks passed - create bound symbol
        bound = BoundSymbol(
            symbol_id=symbol.id,
            symbol_type=symbol.symbol_type,
            effect=symbol.payload,
            weight=self._calculate_weight(symbol, context),
            context_snapshot=context.model_dump(),
        )

        # Record activation
        self.activated_symbols.add(symbol.id)
        self._log(symbol.id, SymbolState.DORMANT, SymbolState.ACTIVATED, "Binding success")

        # Record success in audit trail
        attempt = BindingAttempt(
            symbol_id=symbol.id,
            context_snapshot=context.model_dump(),
            success=True,
            bound_symbol_id=symbol.id,
        )
        self.streaming.record_attempt(attempt)

        # Fire event hook if registered
        if self.on_symbol_activated:
            self.on_symbol_activated(symbol, context, bound)

        return bound

    def bind_all(self, symbol_ids: List[str], context: Context) -> List[BoundSymbol]:
        """Bind multiple symbols sequentially (simple order, no dependency resolution)."""
        results: List[BoundSymbol] = []
        for sym_id in symbol_ids:
            symbol = self.symbol_registry[sym_id]
            bound = self.bind(symbol, context)
            if bound is not None:
                results.append(bound)
        return results

    def bind_all_registered(
        self,
        context: Context,
        max_iterations: int = 10,
        apply_state_mutations: bool = True
    ) -> Tuple[List[BoundSymbol], Context]:
        """Attempt to bind all registered symbols with dependency cascade.

        Only attempts symbols whose preconditions are met:
        - Dependencies must be satisfied (all deps in activated_symbols)
        - Temporal conditions must allow binding (no future-only gates)
        - State conditions must be satisfied (gate.state matches context.state)

        Symbols that fail preconditions remain LATENT (not attempted, no audit entry).

        Args:
            context: Runtime context for binding
            max_iterations: Maximum cascade rounds (prevents infinite loops)
            apply_state_mutations: If True (default), state mutations from bound symbols
                are applied to context between rounds, enabling reactive state-driven chains.
                If False, state mutations are recorded but not applied (analytical mode).

        Returns:
            Tuple of (bound_symbols, final_context)
            - bound_symbols: List of successfully bound symbols
            - final_context: Context after all state mutations (same as input if apply_state_mutations=False)

        Note:
            Context is immutable (frozen). State mutations create new Context instances.
            Last-write-wins for conflicting state mutations within same round.
        """
        results: List[BoundSymbol] = []
        consumed_ids = set()  # Track one_shot symbols that have been consumed
        current_context = context  # Track evolving context

        # Multi-pass iteration to handle dependency cascades
        for iteration in range(max_iterations):
            bound_this_iteration = []

            # Try to bind each symbol (skip consumed one_shot symbols)
            for sym_id, symbol in self.symbol_registry.items():
                # Skip if one_shot symbol already consumed
                if sym_id in consumed_ids:
                    continue

                # Pre-checks: Only attempt symbols whose preconditions are met.
                # Symbols failing pre-checks remain LATENT (no attempt, no audit entry).
                # Uses checker.matches() to ensure single source of truth for gate logic.
                dep_checker = DependencyChecker(self.activated_symbols)
                if not dep_checker.matches(symbol, current_context):
                    continue

                if not WhenChecker().matches(symbol, current_context):
                    continue

                if not StateChecker().matches(symbol, current_context):
                    continue

                if not WhoChecker().matches(symbol, current_context):
                    continue

                if not WhereChecker().matches(symbol, current_context):
                    continue

                # All preconditions satisfied - attempt binding
                bound = self.bind(symbol, current_context)
                if bound is not None:
                    bound_this_iteration.append(bound)

                    # Consumption mode handling
                    if symbol.consumption == "one_shot":
                        # Default: ticket burns after binding
                        consumed_ids.add(sym_id)
                    elif symbol.consumption == "reusable":
                        # Reusable: symbol can bind again in future rounds
                        pass  # Not added to consumed_ids

            # Stop if no progress made (no symbols bound this round)
            if not bound_this_iteration:
                break

            results.extend(bound_this_iteration)

            # Apply state mutations from this round (if enabled)
            if apply_state_mutations:
                for bound_symbol in bound_this_iteration:
                    if 'state_mutation' in bound_symbol.effect:
                        state_changes = []
                        # Apply each state mutation (last-write-wins for conflicts)
                        for key, value in bound_symbol.effect['state_mutation'].items():
                            old_value = current_context.state.get(key)
                            state_changes.append({
                                "key": key,
                                "old": old_value,
                                "new": value
                            })
                            current_context = current_context.with_state_update(key, value)

                        # Track state changes in bound symbol for audit trail
                        bound_symbol.state_changes_applied = state_changes

                        # Update audit trail with state changes
                        self._update_audit_with_state_changes(bound_symbol.symbol_id, state_changes)

        return results, current_context

    def _update_audit_with_state_changes(self, symbol_id: str, state_changes: List[Dict[str, Any]]) -> None:
        """Update audit trail entry with state changes that were applied.

        Finds the most recent successful BindingAttempt for the given symbol_id
        and replaces it with a new one that includes state_changes_applied.

        Args:
            symbol_id: Symbol ID to update audit for
            state_changes: List of state changes to record
        """
        # Find the most recent successful attempt for this symbol
        for i in range(len(self.audit.trail) - 1, -1, -1):
            entry = self.audit.trail[i]
            if entry.symbol_id == symbol_id and entry.success:
                # Create new BindingAttempt with state_changes_applied
                updated_entry = BindingAttempt(
                    symbol_id=entry.symbol_id,
                    attempt_timestamp=entry.attempt_timestamp,
                    context_snapshot=entry.context_snapshot,
                    success=entry.success,
                    bound_symbol_id=entry.bound_symbol_id,
                    failure_reasons=entry.failure_reasons,
                    state_changes_applied=state_changes
                )
                # Replace the old entry
                self.audit.trail[i] = updated_entry
                break

    def bind_with_state_evolution(
        self,
        ctx: Context,
        max_rounds: int = 10,
        on_round_complete: Optional[Callable[['BindingEngine', Context, int], Context]] = None
    ) -> Tuple[Context, int]:
        """Bind repeatedly until convergence, allowing state evolution between rounds.

        Note: This method uses apply_state_mutations=True by default, so state mutations
        are automatically applied between rounds. The on_round_complete callback can be
        used for additional custom state updates.
        """
        current_ctx = ctx

        # Iterate until convergence (no new symbols activate)
        for round_num in range(max_rounds):
            initial_count = len(self.activated_symbols)
            _, current_ctx = self.bind_all_registered(current_ctx)  # Unpack tuple, get updated context

            # Check for convergence
            if len(self.activated_symbols) == initial_count:
                break

            # Hook: Allow app to update state between rounds
            if on_round_complete:
                current_ctx = on_round_complete(self, current_ctx, round_num)

        return current_ctx, round_num + 1

    def _calculate_weight(self, symbol: LatentSymbol, context: Context) -> float:
        """Compute symbol weight (default: payload['weight'] or 1.0)."""
        return float(symbol.payload.get("weight", 1.0))

    def _log(
        self,
        symbol_id: str,
        from_state: SymbolState,
        to_state: SymbolState,
        reason: str,
    ) -> None:
        """Record a state transition in the ledger."""
        transition = StateTransition(
            symbol_id=symbol_id,
            from_state=from_state,
            to_state=to_state,
            reason=reason,
        )
        self.ledger.append(transition)

    def get_ledger(self, symbol_id: Optional[str] = None) -> List[StateTransition]:
        """Return all recorded transitions or filter by symbol identifier."""
        if symbol_id is None:
            return list(self.ledger)
        return [t for t in self.ledger if t.symbol_id == symbol_id]

    def _validate_acyclic(self) -> None:
        """Validate dependency graph has no cycles using DFS."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node: str, path: List[str]) -> Optional[List[str]]:
            """DFS helper that returns cycle path if found."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            # Check all dependencies
            for neighbor in self.dependency_graph.get(node, []):
                if neighbor not in visited:
                    cycle = dfs(neighbor, path)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found a cycle - build the cycle path
                    cycle_start_idx = path.index(neighbor)
                    return path[cycle_start_idx:] + [neighbor]

            rec_stack.remove(node)
            path.pop()
            return None

        # Check all nodes
        for node in self.dependency_graph:
            if node not in visited:
                cycle = dfs(node, [])
                if cycle:
                    cycle_path = " → ".join(cycle)
                    raise CircularDependencyError(
                        f"Circular dependency detected: {cycle_path}"
                    )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit (auto-close streaming)."""
        self.streaming.close()
        return False
