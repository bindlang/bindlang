"""Tests for composition operators (| alternative)."""

import pytest
from datetime import datetime

from bindlang import (
    BindingEngine,
    LatentSymbol,
    GateCondition,
    Context,
    sym,
    Sym,
    Alternative,
    Sequential,
    Parallel,
    BindingResult,
    BindingStatus,
)


@pytest.fixture
def engine():
    return BindingEngine()


@pytest.fixture
def context_admin():
    return Context(
        who="admin",
        where="app",
        when=datetime.now(),
        state={}
    )


@pytest.fixture
def context_user():
    return Context(
        who="user",
        where="app",
        when=datetime.now(),
        state={}
    )


class TestSymWrapper:
    """Tests for Sym wrapper."""

    def test_sym_wraps_symbol(self):
        symbol = LatentSymbol(
            id="test",
            symbol_type="TEST:basic",
            gate=GateCondition()
        )
        wrapped = sym(symbol)
        assert wrapped.symbol is symbol

    def test_sym_try_bind_success(self, engine, context_admin):
        symbol = LatentSymbol(
            id="test",
            symbol_type="TEST:basic",
            gate=GateCondition(who={"admin"})
        )
        engine.register(symbol)
        wrapped = sym(symbol)

        result = wrapped.try_bind(context_admin, engine)

        assert result.is_bound
        assert result.status == BindingStatus.BOUND
        assert result.bound is not None
        assert result.bound.symbol_id == "test"

    def test_sym_try_bind_latent(self, engine, context_user):
        symbol = LatentSymbol(
            id="admin_only",
            symbol_type="TEST:admin",
            gate=GateCondition(who={"admin"})
        )
        engine.register(symbol)
        wrapped = sym(symbol)

        result = wrapped.try_bind(context_user, engine)

        assert not result.is_bound
        assert result.status == BindingStatus.LATENT
        assert result.source is symbol


class TestAlternativeOperator:
    """Tests for | operator."""

    def test_alternative_first_binds(self, engine, context_admin):
        primary = LatentSymbol(
            id="primary",
            symbol_type="TEST:primary",
            gate=GateCondition(who={"admin"})
        )
        fallback = LatentSymbol(
            id="fallback",
            symbol_type="TEST:fallback",
            gate=GateCondition(who={"user"})
        )
        engine.register(primary)
        engine.register(fallback)

        composed = sym(primary) | sym(fallback)
        result = composed.try_bind(context_admin, engine)

        assert result.is_bound
        assert result.bound.symbol_id == "primary"

    def test_alternative_fallback_binds(self, engine, context_user):
        primary = LatentSymbol(
            id="primary",
            symbol_type="TEST:primary",
            gate=GateCondition(who={"admin"})
        )
        fallback = LatentSymbol(
            id="fallback",
            symbol_type="TEST:fallback",
            gate=GateCondition(who={"user"})
        )
        engine.register(primary)
        engine.register(fallback)

        composed = sym(primary) | sym(fallback)
        result = composed.try_bind(context_user, engine)

        assert result.is_bound
        assert result.bound.symbol_id == "fallback"

    def test_alternative_both_latent(self, engine):
        context_guest = Context(
            who="guest",
            where="app",
            when=datetime.now(),
            state={}
        )
        primary = LatentSymbol(
            id="primary",
            symbol_type="TEST:primary",
            gate=GateCondition(who={"admin"})
        )
        fallback = LatentSymbol(
            id="fallback",
            symbol_type="TEST:fallback",
            gate=GateCondition(who={"user"})
        )
        engine.register(primary)
        engine.register(fallback)

        composed = sym(primary) | sym(fallback)
        result = composed.try_bind(context_guest, engine)

        assert not result.is_bound
        assert result.status == BindingStatus.LATENT

    def test_alternative_chain_three(self, engine):
        context_guest = Context(
            who="guest",
            where="app",
            when=datetime.now(),
            state={}
        )
        first = LatentSymbol(
            id="first",
            symbol_type="TEST:first",
            gate=GateCondition(who={"admin"})
        )
        second = LatentSymbol(
            id="second",
            symbol_type="TEST:second",
            gate=GateCondition(who={"user"})
        )
        third = LatentSymbol(
            id="third",
            symbol_type="TEST:third",
            gate=GateCondition(who={"guest"})
        )
        engine.register(first)
        engine.register(second)
        engine.register(third)

        composed = sym(first) | sym(second) | sym(third)
        result = composed.try_bind(context_guest, engine)

        assert result.is_bound
        assert result.bound.symbol_id == "third"


class TestAlternativeAssociativity:
    """Test that | is associative: (a | b) | c == a | (b | c)."""

    def test_associativity_left(self, engine, context_user):
        a = LatentSymbol(id="a", symbol_type="TEST:a", gate=GateCondition(who={"admin"}))
        b = LatentSymbol(id="b", symbol_type="TEST:b", gate=GateCondition(who={"user"}))
        c = LatentSymbol(id="c", symbol_type="TEST:c", gate=GateCondition(who={"guest"}))
        engine.register(a)
        engine.register(b)
        engine.register(c)

        left_assoc = (sym(a) | sym(b)) | sym(c)
        result = left_assoc.try_bind(context_user, engine)

        assert result.bound.symbol_id == "b"

    def test_associativity_right(self, engine, context_user):
        a = LatentSymbol(id="a2", symbol_type="TEST:a", gate=GateCondition(who={"admin"}))
        b = LatentSymbol(id="b2", symbol_type="TEST:b", gate=GateCondition(who={"user"}))
        c = LatentSymbol(id="c2", symbol_type="TEST:c", gate=GateCondition(who={"guest"}))
        engine.register(a)
        engine.register(b)
        engine.register(c)

        right_assoc = sym(a) | (sym(b) | sym(c))
        result = right_assoc.try_bind(context_user, engine)

        assert result.bound.symbol_id == "b2"


class TestAuditTrail:
    """Test that both attempts are logged."""

    def test_both_attempts_in_audit(self, engine, context_user):
        primary = LatentSymbol(
            id="primary",
            symbol_type="TEST:primary",
            gate=GateCondition(who={"admin"})
        )
        fallback = LatentSymbol(
            id="fallback",
            symbol_type="TEST:fallback",
            gate=GateCondition(who={"user"})
        )
        engine.register(primary)
        engine.register(fallback)

        composed = sym(primary) | sym(fallback)
        composed.try_bind(context_user, engine)

        # Check audit trail has both attempts
        trail = engine.audit.trail
        symbol_ids = [a.symbol_id for a in trail]

        assert "primary" in symbol_ids
        assert "fallback" in symbol_ids


class TestSequentialOperator:
    """Tests for >> operator."""

    def test_sequential_both_bind(self, engine, context_admin):
        gate = LatentSymbol(
            id="gate",
            symbol_type="TEST:gate",
            gate=GateCondition(who={"admin"})
        )
        action = LatentSymbol(
            id="action",
            symbol_type="TEST:action",
            gate=GateCondition(who={"admin"})
        )
        engine.register(gate)
        engine.register(action)

        composed = sym(gate) >> sym(action)
        result = composed.try_bind(context_admin, engine)

        assert result.is_bound
        assert result.bound.symbol_id == "action"

    def test_sequential_first_latent(self, engine, context_user):
        gate = LatentSymbol(
            id="gate",
            symbol_type="TEST:gate",
            gate=GateCondition(who={"admin"})
        )
        action = LatentSymbol(
            id="action",
            symbol_type="TEST:action",
            gate=GateCondition(who={"user"})
        )
        engine.register(gate)
        engine.register(action)

        composed = sym(gate) >> sym(action)
        result = composed.try_bind(context_user, engine)

        assert not result.is_bound
        assert result.source.id == "gate"

    def test_sequential_second_latent(self, engine, context_admin):
        gate = LatentSymbol(
            id="gate",
            symbol_type="TEST:gate",
            gate=GateCondition(who={"admin"})
        )
        action = LatentSymbol(
            id="action",
            symbol_type="TEST:action",
            gate=GateCondition(who={"user"})
        )
        engine.register(gate)
        engine.register(action)

        composed = sym(gate) >> sym(action)
        result = composed.try_bind(context_admin, engine)

        assert not result.is_bound
        assert result.source.id == "action"

    def test_sequential_chain(self, engine, context_admin):
        a = LatentSymbol(id="a", symbol_type="TEST:a", gate=GateCondition(who={"admin"}))
        b = LatentSymbol(id="b", symbol_type="TEST:b", gate=GateCondition(who={"admin"}))
        c = LatentSymbol(id="c", symbol_type="TEST:c", gate=GateCondition(who={"admin"}))
        engine.register(a)
        engine.register(b)
        engine.register(c)

        composed = sym(a) >> sym(b) >> sym(c)
        result = composed.try_bind(context_admin, engine)

        assert result.is_bound
        assert result.bound.symbol_id == "c"


class TestParallelOperator:
    """Tests for & operator."""

    def test_parallel_all_bind(self, engine, context_admin):
        a = LatentSymbol(id="a", symbol_type="TEST:a", gate=GateCondition(who={"admin"}))
        b = LatentSymbol(id="b", symbol_type="TEST:b", gate=GateCondition(who={"admin"}))
        c = LatentSymbol(id="c", symbol_type="TEST:c", gate=GateCondition(who={"admin"}))
        engine.register(a)
        engine.register(b)
        engine.register(c)

        composed = sym(a) & sym(b) & sym(c)
        result = composed.try_bind(context_admin, engine)

        assert result.is_bound
        assert result.bound_all is not None
        assert len(result.bound_all) == 3

    def test_parallel_one_latent(self, engine, context_admin):
        a = LatentSymbol(id="a", symbol_type="TEST:a", gate=GateCondition(who={"admin"}))
        b = LatentSymbol(id="b", symbol_type="TEST:b", gate=GateCondition(who={"user"}))
        c = LatentSymbol(id="c", symbol_type="TEST:c", gate=GateCondition(who={"admin"}))
        engine.register(a)
        engine.register(b)
        engine.register(c)

        composed = sym(a) & sym(b) & sym(c)
        result = composed.try_bind(context_admin, engine)

        assert not result.is_bound
        assert result.source.id == "b"

    def test_parallel_all_latent(self, engine):
        context_guest = Context(who="guest", where="app", when=datetime.now(), state={})
        a = LatentSymbol(id="a", symbol_type="TEST:a", gate=GateCondition(who={"admin"}))
        b = LatentSymbol(id="b", symbol_type="TEST:b", gate=GateCondition(who={"user"}))
        engine.register(a)
        engine.register(b)

        composed = sym(a) & sym(b)
        result = composed.try_bind(context_guest, engine)

        assert not result.is_bound


class TestMixedOperators:
    """Tests for combining operators."""

    def test_alternative_then_sequential(self, engine, context_user):
        admin_gate = LatentSymbol(id="admin_gate", symbol_type="TEST:gate", gate=GateCondition(who={"admin"}))
        user_gate = LatentSymbol(id="user_gate", symbol_type="TEST:gate", gate=GateCondition(who={"user"}))
        action = LatentSymbol(id="action", symbol_type="TEST:action", gate=GateCondition(who={"user"}))
        engine.register(admin_gate)
        engine.register(user_gate)
        engine.register(action)

        composed = (sym(admin_gate) | sym(user_gate)) >> sym(action)
        result = composed.try_bind(context_user, engine)

        assert result.is_bound
        assert result.bound.symbol_id == "action"

    def test_sequential_with_parallel(self, engine, context_admin):
        gate = LatentSymbol(id="gate", symbol_type="TEST:gate", gate=GateCondition(who={"admin"}))
        a = LatentSymbol(id="a", symbol_type="TEST:a", gate=GateCondition(who={"admin"}))
        b = LatentSymbol(id="b", symbol_type="TEST:b", gate=GateCondition(who={"admin"}))
        engine.register(gate)
        engine.register(a)
        engine.register(b)

        composed = sym(gate) >> (sym(a) & sym(b))
        result = composed.try_bind(context_admin, engine)

        assert result.is_bound
        assert result.bound_all is not None
        assert len(result.bound_all) == 2

    def test_parallel_with_fallback(self, engine, context_user):
        admin = LatentSymbol(id="admin", symbol_type="TEST:admin", gate=GateCondition(who={"admin"}))
        user = LatentSymbol(id="user", symbol_type="TEST:user", gate=GateCondition(who={"user"}))
        other = LatentSymbol(id="other", symbol_type="TEST:other", gate=GateCondition(who={"user"}))
        engine.register(admin)
        engine.register(user)
        engine.register(other)

        composed = (sym(admin) | sym(user)) & sym(other)
        result = composed.try_bind(context_user, engine)

        assert result.is_bound
        assert result.bound_all is not None
        assert len(result.bound_all) == 2
