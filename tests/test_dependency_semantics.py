"""
Test dependency chain semantics.

Verifies that symbols failing any precondition (dependencies, gates)
remain LATENT (not attempted, no audit entry).
"""

from datetime import datetime
from bindlang.core.engine import BindingEngine
from bindlang.core.models import LatentSymbol, GateCondition, Context


def test_latent_symbols_not_attempted():
    """Symbols failing any precondition remain LATENT (not attempted)."""
    engine = BindingEngine()

    # Symbol A: Activates for alice
    symbol_a = LatentSymbol(
        id="a",
        symbol_type="TEST:a",
        gate=GateCondition(who={"alice"}),
        payload={}
    )

    # Symbol B: Depends on A, but who gate fails (bob != alice)
    # Remains LATENT because all gates are preconditions
    symbol_b = LatentSymbol(
        id="b",
        symbol_type="TEST:b",
        gate=GateCondition(who={"bob"}),
        payload={},
        depends_on=["a"]
    )

    # Symbol C: Depends on B (which is latent, so dep unsatisfied)
    symbol_c = LatentSymbol(
        id="c",
        symbol_type="TEST:c",
        gate=GateCondition(who={"alice"}),
        payload={},
        depends_on=["b"]
    )

    engine.register(symbol_a)
    engine.register(symbol_b)
    engine.register(symbol_c)

    context = Context(who="alice", where="office", when=datetime.now(), state={})
    results, _ = engine.bind_all_registered(context)

    attempted_ids = {a.symbol_id for a in engine.audit.trail}
    bound_ids = {r.symbol_id for r in results}

    # A binds, B and C remain latent (no audit entry)
    assert bound_ids == {"a"}
    assert attempted_ids == {"a"}


def test_dependency_chain_success():
    """Symbols bind in dependency order when all gates pass."""
    engine = BindingEngine()

    symbol_a = LatentSymbol(
        id="a",
        symbol_type="TEST:a",
        gate=GateCondition(who={"alice"}),
        payload={}
    )

    symbol_b = LatentSymbol(
        id="b",
        symbol_type="TEST:b",
        gate=GateCondition(who={"alice"}),
        payload={},
        depends_on=["a"]
    )

    symbol_c = LatentSymbol(
        id="c",
        symbol_type="TEST:c",
        gate=GateCondition(who={"alice"}),
        payload={},
        depends_on=["b"]
    )

    engine.register(symbol_a)
    engine.register(symbol_b)
    engine.register(symbol_c)

    context = Context(who="alice", where="office", when=datetime.now(), state={})
    results, _ = engine.bind_all_registered(context)

    bound_ids = [r.symbol_id for r in results]
    assert bound_ids == ["a", "b", "c"]


if __name__ == "__main__":
    test_latent_symbols_not_attempted()
    test_dependency_chain_success()
