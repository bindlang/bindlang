"""
Gate condition checkers.

Each checker evaluates one condition type (who, when, where, state, dependency)
and returns structured FailureReason objects.
"""

from __future__ import annotations

from typing import Optional, Protocol, Set

from .models import (
    Context,
    DateTimeTemporal,
    LatentSymbol,
    FailureReason,
    TemporalExpression,
)


class GateChecker(Protocol):
    """Protocol for checking a single gate condition type.

    Each checker evaluates one aspect of a symbol's gate against the
    runtime context.
    """

    def matches(self, symbol: LatentSymbol, context: Context) -> bool:
        """Check if condition is satisfied.

        Returns:
            True if condition passes (or no condition specified), False otherwise
        """
        ...

    def check(self, symbol: LatentSymbol, context: Context) -> Optional[FailureReason]:
        """Check condition and return failure details if not satisfied.

        Returns:
            None if condition passes, FailureReason with details if it fails
        """
        ...


class WhoChecker:
    """Checks if context.who satisfies gate.who condition."""

    def matches(self, symbol: LatentSymbol, context: Context) -> bool:
        if not symbol.gate.who:
            return True
        return context.who in symbol.gate.who

    def check(self, symbol: LatentSymbol, context: Context) -> Optional[FailureReason]:
        if self.matches(symbol, context):
            return None

        return FailureReason(
            condition_type="who",
            expected=sorted(symbol.gate.who),
            actual=context.who,
            message=f"who: '{context.who}' not in {sorted(symbol.gate.who)}"
        )


class WhenChecker:
    """Checks if context.when satisfies gate.when temporal condition."""

    def matches(self, symbol: LatentSymbol, context: Context) -> bool:
        if not symbol.gate.when:
            return True
        try:
            expr = TemporalExpression.parse(symbol.gate.when)
            return expr.evaluate(context)
        except Exception:
            return False

    def check(self, symbol: LatentSymbol, context: Context) -> Optional[FailureReason]:
        if not symbol.gate.when:
            return None

        try:
            expr = TemporalExpression.parse(symbol.gate.when)
            if expr.evaluate(context):
                return None
        except Exception as e:
            return FailureReason(
                condition_type="when",
                expected=symbol.gate.when,
                actual=str(context.when),
                message=f"when: temporal expression '{symbol.gate.when}' evaluation error: {e}"
            )

        return FailureReason(
            condition_type="when",
            expected=symbol.gate.when,
            actual=str(context.when),
            message=f"when: temporal condition '{symbol.gate.when}' not satisfied at {context.when}"
        )


class WhereChecker:
    """Checks if context.where satisfies gate.where condition."""

    def matches(self, symbol: LatentSymbol, context: Context) -> bool:
        if not symbol.gate.where:
            return True
        return context.where in symbol.gate.where

    def check(self, symbol: LatentSymbol, context: Context) -> Optional[FailureReason]:
        if self.matches(symbol, context):
            return None

        return FailureReason(
            condition_type="where",
            expected=sorted(symbol.gate.where),
            actual=context.where,
            message=f"where: '{context.where}' not in {sorted(symbol.gate.where)}"
        )


class StateChecker:
    """Checks if context.state satisfies gate.state conditions."""

    def matches(self, symbol: LatentSymbol, context: Context) -> bool:
        if not symbol.gate.state:
            return True
        for key, expected_value in symbol.gate.state.items():
            if context.state.get(key) != expected_value:
                return False
        return True

    def check(self, symbol: LatentSymbol, context: Context) -> Optional[FailureReason]:
        if not symbol.gate.state:
            return None

        for key, expected_value in symbol.gate.state.items():
            actual_value = context.state.get(key)

            if actual_value != expected_value:
                return FailureReason(
                    condition_type="state",
                    expected={key: expected_value},
                    actual={key: actual_value},
                    message=f"state['{key}']: expected {expected_value}, got {actual_value}"
                )

        return None


class DependencyChecker:
    """Checks if all symbol dependencies have been activated."""

    def __init__(self, activated_symbols: Set[str]):
        """Initialize with current set of activated symbol IDs."""
        self.activated_symbols = activated_symbols

    def matches(self, symbol: LatentSymbol, context: Context) -> bool:
        return all(dep_id in self.activated_symbols for dep_id in symbol.depends_on)

    def check(self, symbol: LatentSymbol, context: Context) -> Optional[FailureReason]:
        if not symbol.depends_on:
            return None

        for dep_id in symbol.depends_on:
            if dep_id not in self.activated_symbols:
                return FailureReason(
                    condition_type="dependency",
                    expected=dep_id,
                    actual="not activated",
                    message=f"dependency '{dep_id}' not yet activated"
                )

        return None


class ExpirationChecker:
    """Checks if symbol has permanently expired due to 'before:' deadline."""

    def matches(self, symbol: LatentSymbol, context: Context) -> bool:
        when = symbol.gate.when
        if not when or not when.startswith("before:"):
            return True
        try:
            expr = TemporalExpression.parse(when)
            if isinstance(expr, DateTimeTemporal) and not expr.evaluate(context):
                return False
        except Exception:
            pass
        return True

    def check(self, symbol: LatentSymbol, context: Context) -> Optional[FailureReason]:
        when = symbol.gate.when
        if not when or not when.startswith("before:"):
            return None

        try:
            expr = TemporalExpression.parse(when)

            # Only mark as expired if it's a hard ISO date (not symbolic state reference)
            if not expr.evaluate(context) and isinstance(expr, DateTimeTemporal):
                return FailureReason(
                    condition_type="expired",
                    expected=f"before {expr.reference}",
                    actual=str(context.when),
                    message=f"symbol expired: deadline '{expr.reference}' has passed"
                )
        except Exception:
            pass

        return None
