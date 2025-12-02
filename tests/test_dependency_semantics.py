"""
Test dependency chain semantics.

Verifies that symbols with unsatisfied dependencies remain LATENT
(not attempted) rather than FAILED (attempted but gate check failed).
"""

from datetime import datetime
from bindlang.core.engine import BindingEngine
from bindlang.core.models import LatentSymbol, GateCondition, Context


def test_latent_symbols_not_attempted():
    """Symbols with unsatisfied dependencies should remain LATENT."""
    engine = BindingEngine()

    # Symbol A: Always activates
    symbol_a = LatentSymbol(
        id="a",
        symbol_type="TEST:a",
        gate=GateCondition(who={"alice"}),
        payload={}
    )

    # Symbol B: Depends on A, but will fail gate check
    symbol_b = LatentSymbol(
        id="b",
        symbol_type="TEST:b",
        gate=GateCondition(who={"bob"}),  # Will fail - we are alice
        payload={},
        depends_on=["a"]
    )

    # Symbol C: Depends on B (which will fail)
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

    # Count states
    attempted_ids = {a.symbol_id for a in engine.audit.trail}
    bound_ids = {r.symbol_id for r in results}
    all_ids = {"a", "b", "c"}
    latent_ids = all_ids - attempted_ids

    print(f"\nResults:")
    print(f"  Bound: {bound_ids}")
    print(f"  Attempted: {attempted_ids}")
    print(f"  Latent (not attempted): {latent_ids}")

    # Verify expected behavior
    assert bound_ids == {"a"}, f"Expected A to bind, got {bound_ids}"
    assert "b" in attempted_ids and "b" not in bound_ids, "Expected B to be attempted and failed"
    assert "c" not in attempted_ids, "Expected C to be LATENT (never attempted)"
    assert latent_ids == {"c"}, f"Expected C to be latent, got {latent_ids}"

    print("\nAll assertions passed")
    print("  A: BOUND (attempted and succeeded)")
    print("  B: FAILED (attempted but gate check failed)")
    print("  C: LATENT (never attempted - dependency not satisfied)")


if __name__ == "__main__":
    test_latent_symbols_not_attempted()
